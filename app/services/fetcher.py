import httpx
import json
import os
from datetime import datetime
from typing import Dict, Any, List

class ArcGISFeatureFetcher:
    def __init__(self, feature_server_url: str):
        self.feature_server_url = feature_server_url
    
    async def fetch_demographic_data(self) -> List[Dict[str, Any]]:
        """Fetch all demographic data from ArcGIS FeatureServer with pagination."""
        all_features = []
        offset = 0
        record_count = 2000 # = Max Record Count per response
        
        async with httpx.AsyncClient() as client:
            while True:
                params = {
                    'where': '1=1',
                    'outFields': 'POPULATION,STATE_NAME',
                    'returnGeometry': 'false',
                    'f': 'json',
                    'resultOffset': offset,
                    'resultRecordCount': record_count
                }
                
                response = await client.get(f"{self.feature_server_url}/0/query", params=params)
                response.raise_for_status()
                
                data = response.json()
                features = data.get('features', [])
                
                if not features:
                    break
                    
                all_features.extend(features)
                
                # If we get fewer records than requested, stop fetching
                if len(features) < record_count:
                    break
                    
                offset += record_count
        
        # Save data to ./data directory
        self._save_data_to_file(all_features)
        
        return all_features
    
    async def fetch_aggregated_by_state(self) -> List[Dict[str, Any]]:
        """Aggregate population data by state from fetched demographic data."""
        raw_data = await self.fetch_demographic_data()
        
        state_populations = {}
        for feature in raw_data:
            attributes = feature.get('attributes', {})
            state = attributes.get('STATE_NAME')
            population = attributes.get('POPULATION', 0)

            if not population: 
                continue 

            if state:
                state_populations[state] = state_populations.get(state, 0) + int(population)
        
        # Format as list of dicts similar to ArcGIS feature format
        aggregated_data = []
        for state, total_pop in state_populations.items():
            aggregated_data.append({
                'attributes': {
                    'STATE_NAME': state,
                    'total_population': total_pop
                }
            })
        
        return aggregated_data
    
    def _save_data_to_file(self, data: List[Dict[str, Any]]) -> None:
        """Save data to JSON file in ./data directory with timestamp."""
        os.makedirs('./data', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'./data/demographic_data_{timestamp}.json'
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Saved {len(data)} records to {filename}")
