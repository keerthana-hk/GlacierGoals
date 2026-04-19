import sqlite3
import os

db_path = os.path.join('instance', 'pixelres_v2.db')
print(f"Connecting to {db_path}...")

try:
    conn = sqlite3.connect(db_path)
    # Check if column exists first to be safe
    cursor = conn.execute('PRAGMA table_info(event)')
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'is_annual' not in columns:
        conn.execute('ALTER TABLE event ADD COLUMN is_annual BOOLEAN DEFAULT 0')
        conn.commit()
        print("Column 'is_annual' successfully added!")
    else:
        print("Column 'is_annual' already exists or no such table.")
        
except Exception as e:
    print("Error:", e)
finally:
    if 'conn' in locals():
        conn.close()
