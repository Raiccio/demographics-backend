import sqlite3
import os

def test_sqlite_operations():
	db_name = "test.db"
	conn = sqlite3.connect(db_name)
	cursor = conn.cursor()

	cursor.execute("CREATE TABLE IF NOT EXISTS state_population(state_name TEXT PRIMARY KEY, population);")
	cursor.execute("""
		INSERT OR REPLACE INTO state_population(state_name, population)
		VALUES
			('California', 39512267),
			('Texas', 29145505),
			('Florida', 21477737),
			('New York', 20201249),
			('Pennsylvania', 13002700);
	""")
	cursor.execute("SELECT * FROM state_population WHERE population >= 20000000;")
	print(cursor.fetchall())

	conn.close()
	os.remove(db_name)

