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


