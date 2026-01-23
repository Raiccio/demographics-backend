import requests
from typing import List, Dict

BASE_URL = (
    "https://services.arcgis.com/P3ePLMYs2RVChkJx/"
    "ArcGIS/rest/services/USA_Census_Counties/FeatureServer/0/query"
)

def fetch_counties(
    batch_size: int = 1000,
    max_records: int = 5000,
) -> List[Dict]:
    """
    Fetch county census features from ArcGIS FeatureServer.
    Returns a list of feature dicts.
    """

    features: List[Dict] = []
    offset = 0

    while True:
        params = {
            "where": "1=1",
            "outFields": "*",
            "f": "json",
            "resultOffset": offset,
            "resultRecordCount": batch_size,
        }

        resp = requests.get(BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        batch = data.get("features", [])
        if not batch:
            break

        features.extend(batch)
        offset += batch_size

        if len(features) >= max_records:
            break

    return features