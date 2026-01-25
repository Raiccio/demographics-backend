# Command-line interface, developer utility, manual execution.
"""
    Manual CLI runner for testing and demonstration of the fetcher and processor modules.
    Not part of production or API.
"""

import asyncio
from datetime import datetime
from app.services.fetcher import ArcGISFeatureFetcher
from app.services.data_processor import DataProcessor
from app.config import Config


async def main():
    console_log_msg("Fetching data...")
    fetcher = ArcGISFeatureFetcher(Config.DEFAULT_FEATURE_SERVER_URL)
    await fetcher.fetch_demographic_data()
    
    console_log_msg("Processing data...")
    processor = DataProcessor(Config.DATA_DIR, Config.STORAGE_DIR)
    processor.process_all_data()

def console_log_msg(message: str = ''):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        print(log_entry.strip()) 

if __name__ == "__main__":
    asyncio.run(main())
