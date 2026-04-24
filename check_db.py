from app import app, db, Resolution
from sqlalchemy import inspect

with app.app_context():
    inspector = inspect(db.engine)
    columns = [c['name'] for c in inspector.get_columns('resolution')]
    print(f"Columns in resolution table: {columns}")
    if 'is_graveyard' in columns:
        print("is_graveyard exists")
    else:
        print("is_graveyard MISSING!")
