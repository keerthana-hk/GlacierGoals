import sqlite3

db_path = 'instance/pixelres_v2.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("Adding fcm_token column to user table...")
try:
    c.execute("ALTER TABLE user ADD COLUMN fcm_token VARCHAR(300) DEFAULT NULL")
    print("Added fcm_token")
except Exception as e:
    print(f"Skipped fcm_token: {e}")

conn.commit()
conn.close()
print("Done!")
