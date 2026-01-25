from fastapi import FastAPI, HTTPException
from typing import List, Optional
import sqlite3
import logging
from pathlib import Path
from app.config import Config
from app.services.scheduler import DemographicsScheduler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Demographics API", description="US State Population Data API")

# Initialize scheduler
scheduler = DemographicsScheduler()

@app.on_event("startup")
async def startup_event():
    """Initialize scheduler on application startup."""
    logger.info("Starting Demographics API...")
    scheduler.start()
    logger.info("Demographics API started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup scheduler on application shutdown."""
    logger.info("Shutting down Demographics API...")
    scheduler.shutdown()
    logger.info("Demographics API shutdown completed")

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

## Testing & demonstration endpoints

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
    - server: a service name as per https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services (e.g., USA_Census_Counties, USA_County_Boundaries, Crime, etc.)
    - type: type of server (feature, map or scene)
    - layer: server layer (0, 1, etc.)
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

## Scheduler endpoints

@app.get("/api/scheduler/status")
async def get_scheduler_status():
    """Get comprehensive scheduler status and job information."""
    try:
        status = scheduler.get_job_status()
        
        # Add configuration details
        status["configuration"] = {
            "fetch_interval_seconds": Config.SCHEDULER_FETCH_INTERVAL,
            "fetch_interval_hours": Config.SCHEDULER_FETCH_INTERVAL / 3600,
            "process_interval_seconds": Config.SCHEDULER_PROCESS_INTERVAL,
            "process_interval_hours": Config.SCHEDULER_PROCESS_INTERVAL / 3600,
            "feature_server_url": Config.DEFAULT_FEATURE_SERVER_URL
        }
        
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler status: {str(e)}")

@app.post("/api/scheduler/jobs/{job_id}/trigger")
async def trigger_job(job_id: str):
    """Manually trigger a specific scheduled job."""
    try:
        result = scheduler.trigger_job_manually(job_id)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail= f"Failed to trigger job: {str(e)}")

@app.get("/api/scheduler/config")
async def get_scheduler_config():
    """Get current scheduler configuration (read-only)."""
    return {
        "scheduler": {
            "enabled": Config.SCHEDULER_ENABLED.lower() == 'true',
            "fetch_interval_seconds": Config.SCHEDULER_FETCH_INTERVAL,
            "fetch_interval_hours": Config.SCHEDULER_FETCH_INTERVAL / 3600,
            "process_interval_seconds": Config.SCHEDULER_PROCESS_INTERVAL,
            "process_interval_hours": Config.SCHEDULER_PROCESS_INTERVAL / 3600
        },
        "data_source": {
            "base_arcgis_url": Config.BASE_ARCGIS_API_URL,
            "default_feature_server_url": Config.DEFAULT_FEATURE_SERVER_URL
        },
        "storage": {
            "data_directory": Config.DATA_DIR,
            "storage_directory": Config.STORAGE_DIR,
            "database_file": Config.DB_NAME
        }
    }

@app.post("/api/scheduler/jobs/{job_id}/pause")
async def pause_job(job_id: str):
    """Pause a specific scheduled job."""
    try:
        result = scheduler.pause_job(job_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pause job: {str(e)}")

@app.post("/api/scheduler/jobs/{job_id}/resume")
async def resume_job(job_id: str):
    """Resume a paused scheduled job."""
    try:
        result = scheduler.resume_job(job_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume job: {str(e)}")

@app.delete("/api/scheduler/jobs/{job_id}")
async def remove_job(job_id: str):
    """Remove a scheduled job permanently."""
    try:
        result = scheduler.remove_job(job_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove job: {str(e)}")

@app.get("/api/scheduler/jobs/{job_id}")
async def get_job_details(job_id: str):
    """Get detailed information about a specific job."""
    try:
        result = scheduler.get_job_details(job_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job details: {str(e)}")

