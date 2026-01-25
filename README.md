# Demographics Backend

Production-ready REST API for automated fetching, processing, and serving US demographic data with APScheduler integration.

## Features
- 🔄 **Automated Daily Pipeline** - Scheduled fetching & processing (24h intervals)
- 📊 **RESTful API** - FastAPI-based endpoints for data access
- 🗄️ **SQLite Storage** - Persistent state population database
- ⏰ **Enhanced APScheduler** - Complete job control (pause/resume/remove/trigger)
- 🎮 **Job Management API** - RESTful control of scheduled jobs
- 📈 **ArcGIS Integration** - Direct US Census Counties data access

## Quick Start

### Installation
```bash
git clone <repository>
cd demographics-backend
pip install -r requirements.txt
```

### Start Application
```bash
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Verify Installation
- API Docs: http://localhost:8000/docs
- Scheduler Status: http://localhost:8000/api/scheduler/status
- Health Check: http://localhost:8000/

## API Endpoints

### Data Access
- `GET /api/states/populations` - Get all state populations
- `GET /api/states/{state}/population` - Get specific state population

### Scheduler Management
- `GET /api/scheduler/status` - Comprehensive status with job states
- `GET /api/scheduler/jobs/{job_id}` - Get detailed job information
- `POST /api/scheduler/jobs/{job_id}/pause` - Pause job execution
- `POST /api/scheduler/jobs/{job_id}/resume` - Resume paused job
- `POST /api/scheduler/jobs/{job_id}/trigger` - Manual trigger (auto-resume)
- `DELETE /api/scheduler/jobs/{job_id}` - Remove job until restart
- `GET /api/scheduler/config` - Read-only configuration view

### Manual Control (Testing)
- `POST /api/fetch-data` - Manual data fetching
- `POST /api/process-data` - Manual data processing

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   APScheduler   │    │   ArcGIS API    │
│   REST API      │    │   Background    │    │   FeatureServer │
│                 │    │   Jobs          │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Business Logic Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Fetcher   │  │  Processor  │  │    Scheduler            │  │
│  │   (ArcGIS)  │  │ (Database)  │  │   (Job Management)      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Storage Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  SQLite DB  │  │   JSON      │  │      Log Files          │  │
│  │   (States)  │  │   Files     │  │      (Monthly)          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Configuration

### Scheduler Settings (`app/config.py`)
```python
# Daily intervals by default
SCHEDULER_FETCH_INTERVAL = 86400    # 24 hours (seconds)
SCHEDULER_PROCESS_INTERVAL = 86400  # 24 hours (seconds)
SCHEDULER_ENABLED = 'true'          # Enable/disable scheduler
```

### ArcGIS Configuration
```python
BASE_ARCGIS_API_URL = "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/"
DEFAULT_FEATURE_SERVER_URL = "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/USA_Census_Counties/FeatureServer/0"
```

## Automated Data Pipeline

### Daily Execution Flow
1. **Fetch Job** (Daily):
   - Connects to ArcGIS FeatureServer
   - Downloads county-level demographic data
   - Saves to timestamped JSON files in `./data/`

2. **Process Job** (Daily):
   - Validates and processes latest data files
   - Aggregates county data by state
   - Updates SQLite database with state populations
   - Archives processed files to `./data/processed/`

### Manual Control
Both fetching and processing can be triggered manually via API endpoints for testing and maintenance.

## File Structure
```
demographics-backend/
├── app/
│   ├── api/main.py           # FastAPI application & scheduler init
│   ├── services/
│   │   ├── fetcher.py        # ArcGIS data fetching
│   │   ├── data_processor.py # Data processing & database
│   │   └── scheduler.py      # APScheduler integration + job control
│   ├── config.py             # Application configuration
│   └── storage/
│       ├── demographics.db    # SQLite database
│       └── *.log             # Monthly processing logs
├── data/
│   ├── processed/            # Archived processed files
│   ├── error/                # Failed processing files
│   └── *.json               # Raw fetched data
├── tests/                    # Unit tests
├── requirements.txt          # Dependencies
└── README.md                # This file
```

## Deployment

### Development
```bash
uvicorn app.api.main:app --reload
```

### Production
```bash
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Testing
```bash
pytest tests/ -v
```

## Technology Stack

|     Component     |      Technology      |            Purpose             |
|-------------------|----------------------|--------------------------------|
| **Web Framework** | FastAPI              | REST API development           |
| **Database**      | SQLite               | Lightweight persistent storage |
| **Scheduler**     | APScheduler          | Background job management      |
| **HTTP Client**   | httpx                | Async ArcGIS API calls         |
| **Data Source**   | ArcGIS FeatureServer | US Census demographic data     |

## Data Flow

1. **Automated Fetching** (Every 24 hours):
   ```
   ArcGIS API → Raw JSON Files → Data Validation
   ```

2. **Automated Processing** (Every 24 hours):
   ```
   Raw Files → State Aggregation → SQLite DB → File Archive
   ```

3. **API Requests** (On-demand):
   ```
   Client Request → SQLite Query → JSON Response
   ```

## Monitoring & Logging

### Log Files
- **Processing Logs**: `app/storage/processed_data_YYYYMM.log`
- **Console Output**: Real-time scheduler status

### Health Monitoring
- Scheduler status endpoint provides job health
- API health check endpoint
- Database connectivity verification

## Troubleshooting

### Common Issues

**Scheduler not starting:**
- Check `SCHEDULER_ENABLED = 'true'` in config
- Verify log files for error messages
- Check if another process is using required ports

**Data fetching fails:**
- Verify ArcGIS FeatureServer URL is accessible
- Check network connectivity
- Review logs for specific error messages

**Database errors:**
- Ensure SQLite file has proper permissions
- Check disk space availability
- Verify data directory exists

### Debug Commands
```bash
# Check scheduler status
curl http://localhost:8000/api/scheduler/status

# View configuration
curl http://localhost:8000/api/scheduler/config

# Manual data fetch test
curl -X POST http://localhost:8000/api/fetch-data

# Manual data processing test
curl -X POST http://localhost:8000/api/process-data
```

## API Examples

### Get All States
```bash
curl http://localhost:8000/api/states/populations
```

### Get Specific State
```bash
curl http://localhost:8000/api/states/California/population
```

### Trigger Scheduler Job
```bash
curl -X POST http://localhost:8000/api/scheduler/jobs/fetch_data/trigger
```

## Job Control Examples

### Pause a Job
```bash
curl -X POST http://localhost:8000/api/scheduler/jobs/fetch_data/pause
```
Response: `{"message": "Job 'fetch_data' paused successfully", "status": "paused"}`

### Resume a Job
```bash
curl -X POST http://localhost:8000/api/scheduler/jobs/fetch_data/resume
```
Response: `{"message": "Job 'fetch_data' resumed successfully", "status": "running"}`

### Trigger Paused Job (Auto-Resume if paused/pending)
```bash
curl -X POST http://localhost:8000/api/scheduler/jobs/fetch_data/trigger
```
Response includes `{"auto_resumed": true}` - job automatically resumes

### Remove Job
```bash
curl -X DELETE http://localhost:8000/api/scheduler/jobs/process_data
```
Response includes `"note": "Job will be recreated on application restart"`

### Check Job Status
```bash
curl http://localhost:8000/api/scheduler/status
```
Shows running/paused job counts and individual job states

### Get Job Details
```bash
curl http://localhost:8000/api/scheduler/jobs/fetch_data
```
Returns comprehensive job information including trigger and next run time

### Filter States
```bash
curl "http://localhost:8000/api/states/populations?states=California,Texas,New%20York"
```