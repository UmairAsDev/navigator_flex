import requests
import json
import os
from report_builder import ReportBuilder # Import our printing class

import requests
from report_builder import ReportBuilder

class TariffLoader:
    BASE_URL = "https://tariffs.flexport.com/api/public/v1/candidate-codes"

    def fetch(self, hts_code: str):
        """
        Fetches tariff data for an HTS code directly from the API.
        Returns parsed JSON or None on failure.
        """
        api_url = f"{self.BASE_URL}/{hts_code}"
        ReportBuilder.print_header(f"Fetching data for HTS {hts_code}")

        try:
            response = requests.get(api_url, timeout=10)
            if not response.ok:
                ReportBuilder.print_error(f"HTTP Error {response.status_code}: Could not find HTS {hts_code}.")
                return None
            data = response.json()
            # print(data)
            ReportBuilder.print_status(f"Successfully fetched tariff data for {hts_code}")
            return data
        except requests.exceptions.RequestException as e:
            ReportBuilder.print_error(f"API request failed: {e}")
            return None





# if __name__ == "__main__":
#     TariffLoader().fetch("8708945000")  
    