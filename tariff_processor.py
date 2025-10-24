from datetime import datetime, date

class TariffProcessor:
    """
    Contains all logic for filtering and analyzing tariff data.
    It takes raw data and user inputs, then returns a
    structured analysis.
    """

    def __init__(self):
        """Initializes the processor."""
        pass  # No state needed, methods are pure

    def _check_conditions(self, conditions: list, transport: str, loading_date: date | None) -> bool:
        """
        Private method to check if a code's applicabilityConditions are met.
        """
        if not conditions:
            return True  # No conditions, so it passes

        for condition in conditions:
            field_key = condition.get('fieldKey')
            cond_type = condition.get('__typename')

            # 1. Check Mode of Transport
            if field_key == "MODE_OF_TRANSPORT" and transport != "ANY":
                if condition.get('fieldShouldEqual') != transport:
                    return False  # Transport mode doesn't match

            # 2. Check Loading Date
            elif field_key == "DATE_OF_LOADING":
                if not loading_date:
                    return False  # Rule requires a loading date, user didn't provide one
                
                try:
                    # Convert ISO string to date object for comparison
                    if cond_type == "CustomsTariffLess":
                        threshold = datetime.fromisoformat(condition['threshold'].replace('Z', '+00:00')).date()
                        if not (loading_date < threshold):
                            return False
                    elif cond_type == "CustomsTariffGreater":
                        threshold = datetime.fromisoformat(condition['threshold'].replace('Z', '+00:00')).date()
                        if not (loading_date > threshold):
                            return False
                    elif cond_type == "CustomsTariffBetween":
                        lower = datetime.fromisoformat(condition['lowerBound'].replace('Z', '+00:00')).date()
                        upper = datetime.fromisoformat(condition['upperBound'].replace('Z', '+00:00')).date()
                        if not (lower <= loading_date < upper): # Note: upperBound is often exclusive
                            return False
                except (KeyError, ValueError):
                    print(f"Warning: Could not parse date condition: {condition}")
                    return False # Fail safe

            # 3. Check for Special Program selection
            elif field_key == "CHOSEN_SPIS":
                # We ignore this rule because the user's intent is to *see* all potential
                # programs, not to have them pre-filtered.
                pass 
        return True

    def _is_code_applicable(self, code: dict, country: str, transport: str, entry_date: date, loading_date: date | None) -> bool:
        """
        Private method to check if a single tariff code is applicable.
        """
        try:
            # 1. Check Entry Date
            from_date = datetime.fromisoformat(code['effectiveFrom'].replace('Z', '+00:00')).date()
            to_date = datetime.fromisoformat(code['effectiveTo'].replace('Z', '+00:00')).date()
            
            if not (from_date <= entry_date <= to_date):
                return False

            # 2. Check Country of Origin
            countries = code.get('countriesOfOrigin', [])
            if countries and not any(c['usCustomsCountryCode'] == country for c in countries):
                return False

            # 3. Check Applicability Conditions
            conditions = code.get('applicabilityConditions', [])
            if not self._check_conditions(conditions, transport, loading_date):
                return False
                
        except (KeyError, ValueError) as e:
            # Catch errors if date fields are missing or malformed
            print(f"Warning: Could not parse applicability for code {code.get('codeVariant', {}).get('code')}. Error: {e}")
            return False

        return True

    def _process_other_tariffs(self, tariffs: list) -> dict:
        """
        Separates other tariffs into penalties, exclusions, and
        links them together.
        """
        
        # --- FIX: Convert penaltyRate string to float for comparison ---
        # We use (c['rateInfo'].get('penaltyRate') or 0) to handle missing keys or empty strings
        penalties = [c for c in tariffs if float(c['rateInfo'].get('penaltyRate') or 0) > 0]
        exclusions = [c for c in tariffs if float(c['rateInfo'].get('penaltyRate') or 0) == 0]
        # --- END FIX ---
        
        final_penalties = []
        excluded_penalties = {} # Stores {penalty_code: {"penalty": {...}, "exclusions": [...]}}
        
        # Get a set of all applicable exclusion codes for faster lookup
        exclusion_code_set = {e['codeVariant']['code'] for e in exclusions}
        
        # Track which exclusions we've used to find the neutral ones
        used_exclusion_codes = set()

        for penalty in penalties:
            is_excluded = False
            penalty_code = penalty['codeVariant']['code']
            matching_exclusions = []

            for excluded_by in penalty.get('excludedByCodes', []):
                ex_code = excluded_by.get('code')
                if ex_code in exclusion_code_set:
                    is_excluded = True
                    # Find the full exclusion object to add to our list
                    matching_exclusions.extend([e for e in exclusions if e['codeVariant']['code'] == ex_code])
                    used_exclusion_codes.add(ex_code)
            
            if is_excluded:
                excluded_penalties[penalty_code] = {
                    "penalty": penalty,
                    "exclusions": matching_exclusions
                }
            else:
                final_penalties.append(penalty)

        # Find exclusions that didn't match any active penalty
        neutral_exclusions = [e for e in exclusions if e['codeVariant']['code'] not in used_exclusion_codes]
        
        return {
            "applicable_penalties": final_penalties,
            "excluded_penalties": excluded_penalties,
            "neutral_exclusions": neutral_exclusions
        }


    def analyze_tariffs(self, raw_data: list, country: str, transport: str, entry_date: date, loading_date: date | None) -> dict:
        """
        Filters and structures all relevant tariff information.
        
        Args:
            raw_data: The full list of data from the JSON file.
            country: The user's country of origin.
            transport: The user's mode of transport.
            entry_date: The user's entry date.
            loading_date: The user's loading date.
            
        Returns:
            A dictionary containing the structured analysis.
        """
        
        # 1. Find Primary Commodity Code
        primary_code = next((c for c in raw_data if c.get("type") == "COMMODITY_CODE"), None)
        
        if not primary_code:
            return {"error": "No primary COMMODITY_CODE found."}

        # 2. Find Applicable Special Programs (GSP, FTAs)
        special_programs = [
            rate for rate in primary_code.get('specialRates', [])
            if any(c['usCustomsCountryCode'] == country for c in rate['importProgram']['countriesOfOrigin'])
        ]

        # 3. Find ALL other applicable tariffs
        other_tariffs = [
            code for code in raw_data
            if code.get("type") != "COMMODITY_CODE" and \
               self._is_code_applicable(code, country, transport, entry_date, loading_date)
        ]
        
        # Sort by priority to ensure logic is correct
        other_tariffs.sort(key=lambda x: x.get('priority', 99))
        
        # 4. Process the other tariffs into a smarter structure
        processed_tariffs = self._process_other_tariffs(other_tariffs)

        return {
            "primary": primary_code,
            "special_programs": special_programs,
            "applicable_penalties": processed_tariffs["applicable_penalties"],
            "excluded_penalties": processed_tariffs["excluded_penalties"],
            "neutral_exclusions": processed_tariffs["neutral_exclusions"]
        }
