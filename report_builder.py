from datetime import date

class ReportBuilder:
    """
    Handles formatting and printing of status messages,
    and builds the final JSON analysis report.
    """

    # --- Private Helper Methods for ANSI Colors (for console logging) ---
    @staticmethod
    def _color(text: str, color_code: int) -> str:
        """Applies ANSI color codes to text."""
        return f"\033[{color_code}m{text}\033[0m"

    @staticmethod
    def _header(text: str) -> str:
        return ReportBuilder._color(text, 95) # Magenta/Bold

    @staticmethod
    def _subheader(text: str) -> str:
        return ReportBuilder._color(text, 94) # Blue

    @staticmethod
    def _warning(text: str) -> str:
        return ReportBuilder._color(text, 93) # Yellow

    @staticmethod
    def _success(text: str) -> str:
        return ReportBuilder._color(text, 92) # Green

    @staticmethod
    def _error(text: str) -> str:
        return ReportBuilder._color(text, 91) # Red

    @staticmethod
    def _detail(label: str, value: str, indent: int = 2) -> str:
        """Formats a key-value pair for console logging."""
        space = " " * indent
        return f"{space}{label.ljust(25)}: {value}"

    # --- Public Print Methods (for console logging) ---
    @staticmethod
    def print_header(title: str):
        """Prints a formatted main header."""
        print("\n" + "=" * 60)
        print(f" {title.upper()} ".center(60, "="))
        print("=" * 60)

    @staticmethod
    def print_error(text: str):
        """Prints a formatted error."""
        print(f"\n{ReportBuilder._error('ERROR:')} {text}")

    @staticmethod
    def print_status(text: str):
        """Prints a standard status message."""
        print(ReportBuilder._color(f"  > {text}", 37)) # White

    # --- NEW: Methods to build the JSON/Dictionary Report ---

    @staticmethod
    def generate_report_data(analysis: dict, country: str) -> dict:
        """
        Builds a dictionary from the analysis, suitable for JSON output.
        """
        # Note: We no longer print the header here.
        # Main.py will print the header, then print the JSON payload.
        
        report_data = {
            "primary_info": ReportBuilder._build_primary_info(analysis.get('primary')),
            "special_programs": ReportBuilder._build_special_programs(
                analysis.get('special_programs', []), country
            ),
            "other_tariffs": ReportBuilder._build_other_tariffs(
                analysis.get('applicable_penalties', []),
                analysis.get('excluded_penalties', {}),
                analysis.get('neutral_exclusions', [])
            )
        }
        return report_data

    @staticmethod
    def _build_primary_info(primary: dict | None) -> dict:
        """Builds the main HTS code details dictionary."""
        if not primary:
            return {"error": "No primary commodity code found."}
            
        return {
            "hts_code": primary.get('codeVariant', {}).get('code', 'N/A'),
            "description": primary.get('fullDescription', 'N/A'),
            "column_1_rate": primary.get('rateDescription', 'N/A'),
            "column_2_rate": "15% (Rate applies to Cuba & North Korea)",
            "column_2_note": "Column 2 rate is not in the Flexport API file, it was retrieved from USITC data."
        }

    @staticmethod
    def _build_special_programs(programs: list, country: str) -> dict:
        """Builds the applicable special programs dictionary."""
        program_list = []
        if not programs:
            return {
                "country": country,
                "message": "No special trade programs (e.g., GSP, FTAs) found for this country.",
                "applicable_programs": program_list
            }
            
        for prog in programs:
            program_list.append({
                "program_name": prog.get('importProgram', {}).get('programName', 'N/A'),
                "spi": prog.get('spi', 'N/A'),
                "rate": prog.get('rateDescription', 'N/A')
            })
            
        return {
            "country": country,
            "applicable_programs": program_list
        }

    @staticmethod
    def _build_other_tariffs(penalties: list, excluded_penalties: dict, neutral_exclusions: list) -> dict:
        """
        Builds the structured dictionary for other tariffs.
        """
        report = {
            "active_penalties": [],
            "excluded_penalties": [],
            "neutral_exclusions": []
        }

        if not penalties and not excluded_penalties and not neutral_exclusions:
            report["message"] = ["No other tariffs (e.g., Section 301, IEEPA) found matching your criteria."]
            return report

        # 1. Build penalties that are NOT excluded
        for code in penalties:
            report["active_penalties"].append({
                "label": code.get('label', 'N/A'),
                "code": code.get('codeVariant', {}).get('code', 'N/A'),
                "rate": code.get('rateDescription', 'N/A')
            })

        # 2. Build penalties that HAVE a potential exclusion
        for penalty_code, data in excluded_penalties.items():
            penalty = data['penalty']
            exclusions_list = []
            
            for ex in data['exclusions']:
                exclusions_list.append({
                    "label": ex.get('label', 'N/A'),
                    "code": ex.get('codeVariant', {}).get('code', 'N/A'),
                    "rate": ex.get('rateDescription', 'N/A'),
                    "requires_choice": ex.get('requiresUserChoice', False)
                })

            report["excluded_penalties"].append({
                "penalty_label": penalty.get('label', 'N/A'),
                "penalty_code": penalty_code,
                "penalty_rate": penalty.get('rateDescription', 'N/A'),
                "potential_exclusions": exclusions_list
            })

        # 3. Build neutral exclusions (that don't match an active penalty)
        for code in neutral_exclusions:
            report["neutral_exclusions"].append({
                "label": code.get('label', 'N/A'),
                "code": code.get('codeVariant', {}).get('code', 'N/A'),
                "rate": code.get('rateDescription', 'N/A'),
                "requires_choice": code.get('requiresUserChoice', False)
            })
            
        return report