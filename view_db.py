import sqlite3

conn = sqlite3.connect("interview.db")
cursor = conn.cursor()

print("\n👤 USERS:\n")
cursor.execute("SELECT * FROM users")
print(cursor.fetchall())

print("\n📌 INTERVIEWS:\n")
cursor.execute("SELECT * FROM interviews")
print(cursor.fetchall())

print("\n⭐ SCORES:\n")
cursor.execute("SELECT * FROM scores")
print(cursor.fetchall())

conn.close()