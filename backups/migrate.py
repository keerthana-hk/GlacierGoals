from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE user ADD COLUMN pet_health INTEGER DEFAULT 100"))
    except:
        pass
    try:
        db.session.execute(text("ALTER TABLE resolution ADD COLUMN is_graveyard BOOLEAN DEFAULT 0"))
    except:
        pass
    try:
        db.session.execute(text("ALTER TABLE resolution ADD COLUMN graveyard_reason TEXT"))
    except:
        pass
    
    db.session.commit()
    db.create_all()
    print("Migration complete!")
    import os
    os._exit(0)
