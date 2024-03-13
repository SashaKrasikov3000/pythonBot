import sqlite3
con = sqlite3.connect("Camsparts.db")
cursor = con.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER, username TEXT, is_admin BOOLEAN, settings TEXT, PRIMARY KEY (id))")
cursor.execute("CREATE TABLE IF NOT EXISTS log (id INTEGER, username TEXT, request TEXT, exception TEXT, time TEXT, PRIMARY KEY (id))")
con.close()