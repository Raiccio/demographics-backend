import os
from typing import Optional


class Config:
    # ArcGIS FeatureServer Configuration
    BASE_ARCGIS_API_URL  = "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/"
    DEFAULT_FEATURE_SERVER_URL  = f"{BASE_ARCGIS_API_URL}USA_Census_Counties/FeatureServer/0"
    
    # Scheduler Configuration
    SCHEDULER_FETCH_INTERVAL = 1800 # 30 minutes
    SCHEDULER_PROCESS_INTERVAL = 3600  # 1 hour
    SCHEDULER_ENABLED = 'true'
    
    # Data Directories
    DATA_DIR = './data'
    STORAGE_DIR = './app/storage'
    DB_NAME = 'demographics.db'
    
    # API Configuration
    API_HOST = '0.0.0.0'
    API_PORT = '8000'