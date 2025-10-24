# import sys
# from datetime import datetime, date
# from tariff_loader import TariffLoader
# from tariff_processor import TariffProcessor
# from report_builder import ReportBuilder

# def get_user_inputs() -> dict:
#     """
#     Prompts the user for all necessary inputs.
    
#     Returns:
#         A dictionary containing all user inputs.
#     """
#     print("Please provide your shipment details.")
    
#     hts_code = input("Enter HTS Code (e.g., 0101300000): ").strip()
#     if not hts_code:
#         ReportBuilder.print_error("HTS Code is required.")
#         sys.exit(1)

#     country_code = input("Enter 2-letter Country of Origin (e.g., AU, CN, MX): ").strip().upper()
#     if not country_code:
#         ReportBuilder.print_error("Country of Origin is required.")
#         sys.exit(1)
    
#     # Default to today's date
#     today_str = date.today().isoformat()
#     entry_date_str = input(f"Enter Entry Date (YYYY-MM-DD) [default: {today_str}]: ").strip() or today_str
    
#     loading_date_str = input("Enter Loading Date (YYYY-MM-DD) [optional, press Enter to skip]: ").strip()
    
#     transport = input("Mode of Transport (ANY, OCEAN, AIR, TRUCK, RAIL) [default: ANY]: ").strip().upper() or "ANY"
    
#     # Validate Transport
#     if transport not in ["ANY", "OCEAN", "AIR", "TRUCK", "RAIL"]:
#         ReportBuilder._warning("Invalid transport mode. Defaulting to 'ANY'.")
#         transport = "ANY"

#     return {
#         "hts_code": hts_code,
#         "country": country_code,
#         "entry_date_str": entry_date_str,
#         "loading_date_str": loading_date_str,
#         "transport": transport,
#         "json_filename": f"{hts_code}_tariff.json" # Create a unique filename
#     }

# def run() -> dict:
#     """
#     Orchestrates the entire application flow and returns structured data.
    
#     Returns:
#         A dictionary containing the structured analysis.
#     """
#     # 1. Get Inputs
#     inputs = get_user_inputs()
    
#     # 2. Validate and Convert Dates
#     try:
#         entry_date = datetime.strptime(inputs['entry_date_str'], '%Y-%m-%d').date()
#     except ValueError:
#         ReportBuilder.print_error(f"Invalid Entry Date format: {inputs['entry_date_str']}. Please use YYYY-MM-DD.")
#         sys.exit(1)
        
#     loading_date = None
#     if inputs['loading_date_str']:
#         try:
#             loading_date = datetime.strptime(inputs['loading_date_str'], '%Y-%m-%d').date()
#         except ValueError:
#             ReportBuilder.print_error(f"Invalid Loading Date format: {inputs['loading_date_str']}. Please use YYYY-MM-DD.")
#             sys.exit(1)

#     # 3. Load/Fetch Data
#     loader = TariffLoader()
#     raw_data = loader.fetch(inputs['hts_code'])
#     if not raw_data:
#         ReportBuilder.print_error(f"No data found for HTS code {inputs['hts_code']}")
#         sys.exit(1)
        
#     # 4. Process and Display Results
#     processor = TariffProcessor()
#     analysis = processor.analyze_tariffs(
#         raw_data,
#         inputs['country'],
#         inputs['transport'],
#         entry_date,
#         loading_date
#     )
    
#     if "error" in analysis:
#         ReportBuilder.print_error(analysis["error"])
#         sys.exit(1)
        
#     # Print the report
#     ReportBuilder.print_report(analysis, inputs['country'])
    
#     # Return the structured analysis
#     return {
#         "inputs": inputs,
#         "analysis": analysis
#     }

# # --- Main execution block ---
# if __name__ == "__main__":
#     try:
#         result = run()
#         print("\nStructured Output:")
#         print(result)
#     except KeyboardInterrupt:
#         ReportBuilder.print_error("\nOperation cancelled by user.")
#         sys.exit(0)