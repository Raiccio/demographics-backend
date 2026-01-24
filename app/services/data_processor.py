import os
import json
import sqlite3
import shutil
import re
from datetime import datetime
from typing import List, Dict, Optional, Union
from pathlib import Path


class DataProcessor:
    def __init__(self, data_dir: str = "./data", storage_dir: str = "./app/storage"):
        self.data_dir = Path(data_dir)
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.data_dir / "processed").mkdir(exist_ok=True)
        (self.data_dir / "error").mkdir(exist_ok=True)
        
        self.db_path = self.storage_dir / "demographics.db"
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize SQLite database with state_populations table."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS state_populations (
                    state_name TEXT PRIMARY KEY,
                    total_population INTEGER,
                    last_updated TIMESTAMP,
                    source_file TEXT
                )
            """)
            conn.commit()
    
    def find_demographic_files(self) -> List[str]:
        """Find all demographic_data_*.json files in data directory."""
        pattern = r"demographic_data_\d{8}_\d{6}\.json$"
        files = []
        
        for file_path in self.data_dir.glob("demographic_data_*.json"):
            if re.match(pattern, file_path.name):
                files.append(str(file_path))
        
        return files
    
    def extract_timestamp(self, filename: str) -> datetime:
        """Extract timestamp from filename: demographic_data_YYYYMMDD_HHMMSS.json"""
        match = re.search(r'demographic_data_(\d{8})_(\d{6})\.json', filename)
        if not match:
            raise ValueError(f"Invalid filename format: {filename}")
        
        date_part = match.group(1)
        time_part = match.group(2)
        
        return datetime.strptime(date_part + time_part, "%Y%m%d%H%M%S")
    
    def find_latest_file(self, files: List[str]) -> Optional[str]:
        """Find the latest file based on timestamp."""
        if not files:
            return None
        
        latest_file = max(files, key=lambda f: self.extract_timestamp(f))
        return latest_file
    
    def aggregate_by_state(self, data: List[Dict]) -> Dict[str, int]:
        """Aggregate population by state from raw data."""
        state_populations = {}
        
        for feature in data:
            attributes = feature.get('attributes', {})
            state = attributes.get('STATE_NAME')
            population = attributes.get('POPULATION', 0)
            
            if state and isinstance(population, (int, float)):
                state_populations[state] = state_populations.get(state, 0) + int(population)
        
        return state_populations
    
    def update_database(self, aggregated_data: Dict[str, int], source_file: str) -> int:
        """Update database with aggregated state population data."""
        updated_states = 0
        timestamp = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            for state, population in aggregated_data.items():
                conn.execute("""
                    INSERT OR REPLACE INTO state_populations 
                    (state_name, total_population, last_updated, source_file)
                    VALUES (?, ?, ?, ?)
                """, (state, population, timestamp, source_file))
                updated_states += 1
            
            conn.commit()
        
        return updated_states
    
    def archive_files(self, files: List[str], error_files: Optional[List[str]] = None) -> None:
        """Move processed and error files to appropriate directories."""
        # Move processed files
        for file_path in files:
            try:
                filename = Path(file_path).name
                shutil.move(file_path, self.data_dir / "processed" / filename)
            except Exception as e:
                self.log_processing(f"ERROR moving {file_path}: {e}")
        
        # Move error files
        if error_files:
            for file_path in error_files:
                try:
                    filename = Path(file_path).name
                    shutil.move(file_path, self.data_dir / "error" / filename)
                except Exception as e:
                    self.log_processing(f"ERROR moving error file {file_path}: {e}")
    
    def get_log_filename(self) -> str:
        """Get current month log filename."""
        current_month = datetime.now().strftime("%Y%m")
        return str(self.storage_dir / f"processed_data_{current_month}.log")
    
    def log_processing(self, message: str) -> None:
        """Log processing message to monthly log file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        log_file = self.get_log_filename()
        with open(log_file, "a") as f:
            f.write(log_entry)
        
        print(log_entry.strip())  # Also print to console
    
    def validate_json_file(self, file_path: str) -> bool:
        """Validate JSON file format and required fields."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                return False
            
            # Check first few items for required fields
            for i, item in enumerate(data[:5]):
                if not isinstance(item, dict) or 'attributes' not in item:
                    return False
                
                attributes = item['attributes']
                if 'STATE_NAME' not in attributes or 'POPULATION' not in attributes:
                    return False
            
            return True
        except Exception:
            return False
    
    def process_all_data(self) -> bool:
        """Main processing method."""
        try:
            self.log_processing("PROCESSING_START: Starting data processing")
            
            # Find all fetched raw data files 
            files = self.find_demographic_files()
            if not files:
                self.log_processing("NO_FILES: No demographic data files found")
                return False
            
            self.log_processing(f"FILES_FOUND: {len(files)} unprocessed files discovered")
            
            # Validate files
            valid_files = []
            error_files = []
            
            for file_path in files:
                if self.validate_json_file(file_path):
                    valid_files.append(file_path)
                else:
                    error_files.append(file_path)
                    self.log_processing(f"VALIDATION_ERROR: {Path(file_path).name}")
            
            if not valid_files:
                self.log_processing("NO_VALID_FILES: No valid files to process")
                self.archive_files([], error_files)
                return False
            
            # Find latest file
            latest_file = self.find_latest_file(valid_files)
            self.log_processing(f"LATEST_FILE: {Path(latest_file).name}")
            
            # Process latest file
            with open(latest_file, 'r') as f:
                data = json.load(f)
            
            aggregated_data = self.aggregate_by_state(data)
            updated_states  = self.update_database(aggregated_data, Path(latest_file).name)
            
            # Archive all files
            self.archive_files(valid_files, error_files)
            
            self.log_processing(f"DATABASE_UPDATE: {updated_states} states updated from {len(data)} county records")
            self.log_processing(f"FILES_ARCHIVED: {len(valid_files)} files moved to processed/")
            if error_files:
                self.log_processing(f"ERROR_FILES: {len(error_files)} files moved to error/")
            self.log_processing("PROCESSING_SUCCESS: Data processing completed")
            
            return True
            
        except Exception as e:
            self.log_processing(f"PROCESSING_ERROR: {str(e)}")
            return False