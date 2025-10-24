
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import date, datetime
from typing import List
import asyncio
from tariff_loader import TariffLoader
from tariff_processor import TariffProcessor
from report_builder import ReportBuilder
import re
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)    


router = APIRouter()

class TariffRequest(BaseModel):
    hts_code: str
    country: List[str]
    entry_date: date
    loading_date: date | None = None
    mode_of_transport: List[str]
    base_cost: float = 0.0










def extract_values(input_string):
    """
    Extracts all numeric values (including percentages, decimals, or integers) from a string.

    Args:
        input_string (str): The input string to extract values from.

    Returns:
        list: A list of extracted numeric values as strings.
    """
    pattern = r"\d+\.?\d*%?"
    matches = re.findall(pattern, input_string)
    return matches













@router.post("/calculate-tariff", response_class=JSONResponse)
async def calculate_tariff_route(request: TariffRequest):
    try:
        valid_modes = ["ANY", "OCEAN", "AIR", "TRUCK", "RAIL"]
        if request.mode_of_transport[0].upper() not in valid_modes:
            raise HTTPException(status_code=400, detail=f"Invalid mode_of_transport. Must be one of {valid_modes}")

        raw_data = TariffLoader().fetch(request.hts_code)
        if not raw_data:
            raise HTTPException(status_code=404, detail=f"No data found for HTS code {request.hts_code}")

        processor = TariffProcessor()
        analysis = processor.analyze_tariffs(
            raw_data,
            country=request.country[0],
            transport=request.mode_of_transport[0].upper(),
            entry_date=request.entry_date,
            loading_date=request.loading_date
        )

        if "error" in analysis:
            raise HTTPException(status_code=400, detail=analysis["error"])
        
        report_results = ReportBuilder.generate_report_data(analysis, request.country[0])
        print(report_results)
        
        #----------Tariff Calculation Logic (Placeholder)----------
        
        def get_data(report_results: dict):
            """Calculates total tariff based on report results and base cost.
            
            Args:
                report_results: Dictionary containing tariff analysis results.
                base_cost: Base cost for the tariff calculation.
            
            Returns:
                Total calculated tariff as a float.
            """

            primary_info = report_results.get("primary_info", {})
            logging.info(f"Primary Info: {primary_info}")
            special_programs = report_results.get("special_programs", {})
            logging.info(f"Special Programs: {special_programs}")
            other_tariffs = report_results.get("other_tariffs", {})
            logging.info("other_tariffs fetched", other_tariffs)
            neutral_exclusions = other_tariffs.get("neutral_exclusions", [])
            logging.info(f"Neutral Exclusions: {neutral_exclusions}")

            if special_programs.get("applicable_programs"):
                basic_rate = special_programs["applicable_programs"][0].get("rate", "0%")
                logging.info(f"Basic rate from special programs: {basic_rate}")
            else:
                basic_rate = primary_info.get("column_1_rate", "0%")

            penalties = []
            if other_tariffs.get("active_penalties"):
                for penalty in other_tariffs["active_penalties"]:
                    if isinstance(penalty, dict):
                        penalty_label = penalty.get("label", "")
                        penalty_code = penalty.get("code", "")
                        penalty_rate = penalty.get("rate", "")

                        penalties.append({
                            "label": penalty_label,
                            "code": penalty_code,
                            "rate_values": extract_values(penalty_rate)
                        })
                            
                            
            logging.info(f"Penalties: {penalties}")
            excluded_penalties = []
            potential_exclusions = []
            neutral_exclusions = []
            if other_tariffs.get("excluded_penalties"):
                for penalty in other_tariffs["excluded_penalties"]:
                    penalty_label = penalty.get("penalty_label", "")
                    penalty_code = penalty.get("penalty_code", "")
                    penalty_rate = penalty.get("penalty_rate", "")
                    logging.info(f"Penalty Rate: {penalty_rate}")
                    excluded_penalties.append({
                        "code": penalty_code,
                        "rate_values": extract_values(penalty_rate),
                        "label": penalty_label
                    })
                                
          
                    for potential in penalty.get("potential_exclusions", []):
                        rate = potential.get("rate", "")
                        code = potential.get("code", "")
                        label = potential.get("label", "")
                        logging.info(f"Potential Exclusion Rate: {rate}")
                        potential_exclusions.append({
                            "code": code,
                            "rate_values": extract_values(rate),
                            "label": label
                        })
                    
                    for neutral in penalty.get("neutral_exclusions", []):
                        for value in neutral.values():
                            if isinstance(value, str):
                                neutral_exclusions.extend(extract_values(value))
                                logging.info(f"Neutral Exclusion Rate: {value}")
                                
                                
                                              
            return {
                "basic_rate": basic_rate,
                "penalties": penalties,
                "excluded_penalties": excluded_penalties,
                "potential_exclusions": potential_exclusions,
                "neutral_exclusions": neutral_exclusions,
            }
    
        total_tariff = get_data(report_results)
        
        def calculate_total_tariff(tariff_data: dict, base_cost: float):
            """Calculate total tariff percentage"""

            total_rate = 0.0
            active_total_rate = 0.0
            excluded_total_rate = 0.0

            basic_rate_str = tariff_data.get("basic_rate", "0%")
            if isinstance(basic_rate_str, str) and basic_rate_str.lower() == "free":
                basic_rate_value = 0.0
            else:
                values = extract_values(basic_rate_str)
                basic_rate_value = float(values[0].replace('%', '')) if values else 0.0

            total_rate += basic_rate_value
            logging.info(f"Basic Rate Value: {basic_rate_value}")

            for penalty in tariff_data.get("penalties", []):
                for penalty_value in penalty.get("rate_values", []):
                    try:
                        active_total_rate += float(penalty_value.replace('%', ''))
                    except ValueError:
                        pass

            logging.info(f"Active Total Rate: {active_total_rate}")
            for excluded in tariff_data.get("excluded_penalties", []):
                for rate_str in excluded.get("rate_values", []):
                    try:
                        excluded_total_rate += float(rate_str.replace('%', ''))
                    except ValueError:
                        pass
            logging.info(f"Excluded Total Rate: {excluded_total_rate}")
            for neutral_str in tariff_data.get("neutral_exclusions", []):
                try:
                    total_rate += float(neutral_str.replace('%', ''))
                except ValueError:
                    pass


            duty_rate = total_rate + active_total_rate + excluded_total_rate
            total_cost = base_cost * (duty_rate / 100)
            
            

            return {
                "duty_rate": f"{duty_rate:.2f}%",
                "total_duties" : total_cost,
                "total_cost": total_cost + request.base_cost
            }

        
        total_rate = calculate_total_tariff(total_tariff, request.base_cost)
        
        
        return JSONResponse(content={"status": "success", "data": report_results, "total_tariff": total_tariff, "total_rate": total_rate})

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")