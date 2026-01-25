from fastapi import FastAPI, HTTPException
from typing import List, Optional
import sqlite3
from pathlib import Path
from app.config import Config

app = FastAPI(title="Demographics API", description="State Population Data API")

def get_db_connection():
    """Get database connection."""
    db_path = Path("./app/storage/demographics.db")
    return sqlite3.connect(db_path)

@app.get("/")
async def root():
    return {
        "API": "Demographics API - State Population Data",
        "Swagger / OpenAPI docs": "/docs",
    }

@app.get("/api/states/populations")
async def get_all_states(states: Optional[str] = None):
    """Get all state populations or filter by specific states.
    
    Query parameters:
    - states: Comma-separated list of state names (e.g., "California,Texas,New York")
    """
    try:
        with get_db_connection() as conn:
            if states:
                # Filter by specific states, case insensitive, accounting for District of Columbia
                state_list = [s.strip().title().replace(" Of ", " of ") 
                              for s in states.split(',') if s.strip()]
                if not state_list:
                    raise HTTPException(status_code=400, detail="Invalid states parameter")
                
                placeholders = ','.join(['?' for _ in state_list])
                query = f"""
                    SELECT state_name, total_population, last_updated, source_file
                    FROM state_populations
                    WHERE state_name IN ({placeholders})
                    ORDER BY state_name
                """
                cursor = conn.execute(query, state_list)
            else:
                # Get all states
                cursor = conn.execute("""
                    SELECT state_name, total_population, last_updated, source_file
                    FROM state_populations
                    ORDER BY state_name
                """)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "state": row[0],
                    "population": row[1],
                    "last_updated": row[2],
                    "source_file": row[3]
                })
            
            if states and not results:
                raise HTTPException(status_code=404, detail="No states found matching the criteria")
            
            return {"states": results, "total": len(results)}
    
    except HTTPException:
        raise
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/states/{state_name}/population")
async def get_state_population(state_name: str):
    """Get population for a specific state."""
    # Normalize state name input
    state_name = state_name.title().replace(" Of ", " of ")
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("""
                SELECT state_name, total_population, last_updated, source_file
                FROM state_populations
                WHERE state_name = ?
            """, (state_name,))
            
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail=f"State '{state_name}' not found")
            
            return {
                "state": row[0],
                "population": row[1],
                "last_updated": row[2],
                "source_file": row[3]
            }
    
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/process-data")
async def trigger_processing():
    """(for testing and demonstration only) Trigger data processing endpoint."""
    from app.services.data_processor import DataProcessor
    
    try:
        processor = DataProcessor()
        success = processor.process_all_data()
        
        if success:
            return {"message": "Data processing completed successfully"}
        else:
            return {"message": "Data processing failed - check logs for details"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
    
@app.post("/api/fetch-data")
async def trigger_fetching(server: Optional[str] = None, type: str = 'Feature', layer: int = 0):
    """(for testing and demonstration only) Trigger data fetching endpoint.
    
    Query parameters:
    - server: a service name as per https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services (e.g., USA_Census_Counties, USA_County_Boundaries, Crime, etc)
    - type: type of server (feature, map or scene)
    - layer: server layer (0, 1, etc)
    """
    from app.services.fetcher import ArcGISFeatureFetcher
    
    try:
        if server :
            arcgis_api_url = f"{Config.BASE_ARCGIS_API_URL}{server}/{type.title()}Server/{layer}/"
        else:
            arcgis_api_url = Config.DEFAULT_FEATURE_SERVER_URL

        fetcher = ArcGISFeatureFetcher(arcgis_api_url)
        features = await fetcher.fetch_demographic_data()

        if not features:
            message = "Data fetching failed - check logs for details"
        else:
            message = "Data fetching completed successfully"

        return {
            "message": message,
            "url": arcgis_api_url,
            "features_count": len(features)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fetching error: {str(e)}")
