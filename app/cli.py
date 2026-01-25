# Command-line interface, developer utility, manual execution.
"""
    Manual CLI runner for testing and demonstration of the fetcher and processor modules.
    Not part of production or API.
"""

import asyncio
import argparse
from datetime import datetime
from app.services.fetcher import ArcGISFeatureFetcher
from app.services.data_processor import DataProcessor
from app.config import Config


async def main(feature_server_url=None, data_dir=None, storage_dir=None):
    console_log_msg("Fetching data...")
    fetcher = ArcGISFeatureFetcher(feature_server_url or Config.DEFAULT_FEATURE_SERVER_URL)
    await fetcher.fetch_demographic_data()
    
    console_log_msg("Processing data...")
    processor = DataProcessor(
        data_dir or Config.DATA_DIR,
        storage_dir or Config.STORAGE_DIR
    )
    processor.process_all_data()

def console_log_msg(message: str = ''):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        print(log_entry.strip()) 

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manual runner for fetcher and data_processor modules")
    parser.add_argument(        "--url", type=str, help = "ArcGIS endpoint")
    parser.add_argument(   "--data_dir", type=str, help = "Directory containing raw data")
    parser.add_argument("--storage_dir", type=str, help = "Storage directory (database)")
    args = parser.parse_args()

    asyncio.run(main(args.url, args.data_dir, args.storage_dir))

