import sqlite3

db_path = 'instance/pixelres_v2.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("Adding columns...")
for col, col_type, default in [
    ('category', 'VARCHAR(50)', "'General'"),
    ('priority', 'VARCHAR(50)', "'Medium'"),
    ('budget', 'FLOAT', "0.0"),
    ('reward', 'VARCHAR(200)', "''")
]:
    try:
        c.execute(f"ALTER TABLE bucket_goal ADD COLUMN {col} {col_type} DEFAULT {default}")
        print(f"Added {col}")
    except Exception as e:
        print(f"Skipped {col}: {e}")

print("Creating bucket_goal_step table...")
try:
    c.execute("""
    CREATE TABLE bucket_goal_step (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        goal_id INTEGER NOT NULL,
        title VARCHAR(200) NOT NULL,
        is_completed BOOLEAN DEFAULT 0,
        FOREIGN KEY(goal_id) REFERENCES bucket_goal(id)
    )
    """)
    print("Created table bucket_goal_step")
except Exception as e:
    print(f"Skipped table creation: {e}")

conn.commit()
conn.close()
print("Done!")
