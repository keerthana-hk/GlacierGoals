import sqlite3

db_path = 'instance/pixelres_v2.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("Adding name and nickname columns to user table...")
try:
    c.execute("ALTER TABLE user ADD COLUMN name VARCHAR(150) DEFAULT ''")
    c.execute("ALTER TABLE user ADD COLUMN nickname VARCHAR(150) DEFAULT ''")
    print("Added name and nickname")
except Exception as e:
    print(f"Skipped columns or error: {e}")

conn.commit()
conn.close()
print("Done!")
