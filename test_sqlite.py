import sqlite3
import os

db_name = "test.db"
conn = sqlite3.connect(db_name)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS state_population(state_name TEXT PRIMARY KEY, population);")
cursor.execute("""
INSERT OR REPLACE INTO t
VALUES
	(1),;

""")
cursor.execute("SELECT * FROM t WHERE a >= 2;")
print(cursor.fetchall())

conn.close()
os.remove(db_name)

