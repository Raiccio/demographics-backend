import asyncio
import pytest
from app.services.fetcher import ESRIFeatureFetcher

@pytest.mark.asyncio
async def test_fetch():
    fetcher = ESRIFeatureFetcher("https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/USA_Census_Counties/FeatureServer")
    
    try:
        print("Fetching demographic data...")
        data = await fetcher.fetch_demographic_data()
        print(f"Fetched {len(data)} records.")
        
        if data:
            print("Sample record:", data[0])
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_fetch())