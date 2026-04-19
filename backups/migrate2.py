import sqlite3
import os

db_path = 'instance/pixelres_v2.db'
if not os.path.exists(db_path):
    db_path = 'pixelres_v2.db'

conn = sqlite3.connect(db_path)
cur = conn.cursor()
try:
    cur.execute("ALTER TABLE user ADD COLUMN pet_health INTEGER DEFAULT 100")
except Exception as e:
    pass
try:
    cur.execute("ALTER TABLE resolution ADD COLUMN is_graveyard BOOLEAN DEFAULT 0")
except:
    pass
try:
    cur.execute("ALTER TABLE resolution ADD COLUMN graveyard_reason TEXT")
except:
    pass

cur.execute("""
CREATE TABLE IF NOT EXISTS time_capsule (
    id INTEGER NOT NULL PRIMARY KEY, 
    user_id INTEGER NOT NULL, 
    content TEXT NOT NULL, 
    unlock_level INTEGER, 
    created_at DATETIME, 
    is_open BOOLEAN, 
    FOREIGN KEY(user_id) REFERENCES user (id)
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS quest_log (
    id INTEGER NOT NULL PRIMARY KEY, 
    user_id INTEGER NOT NULL, 
    date VARCHAR(10) NOT NULL, 
    story TEXT NOT NULL, 
    FOREIGN KEY(user_id) REFERENCES user (id),
    CONSTRAINT _user_date_quest_uc UNIQUE (user_id, date)
)
""")
conn.commit()
conn.close()
print("Migration done")
