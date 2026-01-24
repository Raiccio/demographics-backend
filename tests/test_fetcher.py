import pytest
from app.services.fetcher import ArcGISFeatureFetcher

@pytest.mark.asyncio
async def test_fetch_demographic_data():
    fetcher = ArcGISFeatureFetcher("https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/USA_Census_Counties/FeatureServer")
    
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
    fetcher = ArcGISFeatureFetcher("https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/USA_Census_Counties/FeatureServer")
    
    print("Fetching population data aggregated by state...")
    aggregated_data = await fetcher.fetch_aggregated_by_state()
    print(f"Fetched {len(aggregated_data)} records.")
    
    print(aggregated_data[0])
    