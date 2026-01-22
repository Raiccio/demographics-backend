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

**1️⃣ Presentation Layer (PL)**

Purpose: interface to clients
Implementation: ***FastAPI***

Responsibilities:

• expose resources (/states, /states?name=Texas)

• validate incoming requests

• call Design Layer to get processed data

Key point: purely stateless, no DB logic here


**2️⃣ Design Layer (DL)**

Purpose: business logic / processing
Implementation : ***Python***

Responsibilities:

• On-demand: handle API requests, transform them into DB queries, aggregate or filter data
• Background job: periodic fetch of ESRI GIS data, aggregation by state, storage in DB
• Decouples client-facing logic from data storage details

Key point: this is the most complex layer, combines request handling and passive background processing

**3️⃣ Storage Layer (SL)**

Purpose: persistent data storage
Implementation: ***SQLite database***

Responsibilities:

• store aggregated demographic data

• expose only structured queries to DL

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











































