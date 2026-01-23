# demographics-backend
Data is fetched from an Esri ArcGIS FeatureServer
using the ArcGIS REST Query API,
which exposes a SQL-like query interface over HTTP.


Aggregation is performed server-side using built-in statistical queries,
reducing network overhead and improving scalability.




| Thing         | Analogy                   |
| ------------- | ------------------------- |
| FeatureServer | Database exposed via HTTP |
| Layer `/0`    | Table                     |
| Fields        | Columns                   |
| OBJECTID      | Primary key               |
| query         | SELECT                    |
| outStatistics | GROUP BY + SUM            |
| JSON          | Result set                |




REST API = HTTP-based interface for manipulating resources

Periodic execution is implemented using an application-level scheduler (APScheduler), avoiding OS-specific dependencies such as cron and ensuring cross-platform compatibility.

## STRUCTURE

**1️⃣ Presentation / API Layer (AL)**

Purpose: interface to clients
Implementation: ***FastAPI***

Responsibilities:
<ul>
  <li>expose resources (/states, /states?name=Texas)</li>
  <li>validate incoming requests</li>
  <li>call Design Layer to get processed data</li>
</ul>

Key point: purely stateless, no DB logic here


**2️⃣ Design / Services Layer (DL)**

Purpose: business logic / processing
Implementation : ***Python***

Responsibilities:
<ul>
  <li>On-demand: handle API requests, transform them into DB queries, aggregate or filter data</li>
  <li>Background job: periodic fetch of ESRI GIS data, aggregation by state, storage in DB</li>
  <li>Decouples client-facing logic from data storage details</li>
</ul>

Key point: this is the most complex layer, combines request handling and passive background processing

**3️⃣ Data / Storage Layer (SL)**

Purpose: persistent data storage
Implementation: ***SQLite database***

Responsibilities:
<ul>
  <li>store aggregated demographic data</li>
  <li>expose only structured queries to DL</li>
</ul>

Key point: no API, no business logic; DL is the only client


      +--------------------+
      |  Presentation Layer|
      |   (REST API)       |
      +---------+----------+
                |
                v
      +--------------------+
      |  Design Layer      |
      |  (Service / Logic) |
      |  - API requests    |
      |  - Background job  |
      +---------+----------+
                |
                v
      +--------------------+
      |  Storage Layer     |
      |  (SQLite DB)       |
      +--------------------+


============


2️⃣ Storage layer first (quick win)
<ul>
<li>Create SQLite DB file demographics.db in data/</li>
<li>Make table state_population(state_name TEXT PRIMARY KEY, population INT, updated_at DATETIME)</li>
<li>Test inserting and querying manually in Python</li>
</ul>
3️⃣ Service layer minimal

Write a function that fetches ESRI JSON and aggregates population by state
Print the result → end-to-end works
Later: write to SQLite

4️⃣ API layer minimal

FastAPI app exposing:

    GET /states → returns all states
    GET /states?name=Texas → returns that state

Test with curl or browser

5️⃣ Background job

Add APScheduler job that calls your ESRI fetch + DB write every X seconds/minutes
Test it prints something → works

6️⃣ Iterate

Once the full path works (fetch → aggregate → store → serve), add:
<ul>
<li>proper exception handling</li>
<li>docstrings</li>
<li>logging</li>
<li>requirements justification in your documentation</li>
</ul>

====================

Structure:
- app/api/ - FastAPI presentation layer (REST endpoints)
- app/services/ - Business logic layer (ESRI data processing)
- app/storage/ - SQLite data storage layer
- data/ - Database files directory
- docs/ - Documentation





































