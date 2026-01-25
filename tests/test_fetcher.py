import pytest
from app.services.fetcher import ArcGISFeatureFetcher
from app.config import Config

@pytest.mark.asyncio
async def test_fetch_demographic_data():
    fetcher = ArcGISFeatureFetcher(Config.DEFAULT_FEATURE_SERVER_URL)
    
    print("Fetching demographic data...")
    data = await fetcher.fetch_demographic_data()
    print(f"Fetched {len(data)} records.")
    
    if data:
        print("Sample record:", data[0])
    
    assert 'attributes' in data[0]
    assert 'POPULATION' in data[0]['attributes']
    assert 'STATE_NAME' in data[0]['attributes']

    
@pytest.mark.asyncio
async def test_fetch_aggregated_by_state():
    fetcher = ArcGISFeatureFetcher(Config.DEFAULT_FEATURE_SERVER_URL)
    
    print("Fetching population data aggregated by state...")
    aggregated_data = await fetcher.fetch_aggregated_by_state()
    print(f"Fetched {len(aggregated_data)} records.")
    
    print(aggregated_data[0])
    

if __name__ == "__main__":
    pytest.main([__file__])