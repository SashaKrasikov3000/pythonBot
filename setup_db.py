import sqlite3
con = sqlite3.connect("Camsparts.db")
cursor = con.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER, username TEXT, is_admin BOOLEAN, settings TEXT, PRIMARY KEY (id))")
cursor.execute("INSERT INTO users (username, is_admin, settings) VALUES ('SashaKrasikov', 1, '00000')") if not cursor.execute("SELECT * FROM users WHERE username = 'SashaKrasikov'").fetchall() else 1
cursor.execute("INSERT INTO users (username, is_admin, settings) VALUES ('krasikov80', 1, '00000')") if not cursor.execute("SELECT * FROM users WHERE username = 'krasikov80'").fetchall() else 1
con.commit()
cursor.execute("CREATE TABLE IF NOT EXISTS log (id INTEGER, username TEXT, request TEXT, exception TEXT, time TEXT, PRIMARY KEY (id))")
con.close()