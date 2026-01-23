import httpx
import json
from typing import Dict, Any, List

class ESRIFeatureFetcher:
    def __init__(self, feature_server_url: str):
        self.feature_server_url = feature_server_url
    
    async def fetch_demographic_data(self) -> List[Dict[str, Any]]:
        """Fetch all demographic data from ESRI FeatureServer with pagination."""
        all_features = []
        offset = 0
        record_count = 2000
        
        async with httpx.AsyncClient() as client:
            while True:
                params = {
                    'where': '1=1',
                    'outFields': '*',
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
                
                # If we got fewer records than requested, we're done
                if len(features) < record_count:
                    break
                    
                offset += record_count
        
        return all_features
    
    async def fetch_aggregated_by_state(self) -> List[Dict[str, Any]]:
        """Fetch population data aggregated by state using ESRI statistics."""
        async with httpx.AsyncClient() as client:
            params = {
                'where': '1=1',
                'outStatistics': json.dumps([
                    {
                        'statisticType': 'sum',
                        'onStatisticField': 'POPULATION',
                        'outStatisticFieldName': 'total_population'
                    },
                    {
                        'statisticType': 'first',
                        'onStatisticField': 'STATE_NAME',
                        'outStatisticFieldName': 'state_name'
                    }
                ]),
                'groupByFieldsForStatistics': 'STATE_NAME',
                'f': 'json'
            }
            
            response = await client.get(f"{self.feature_server_url}/0/query", params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get('features', [])