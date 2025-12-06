"""
Add Strategy1 Entry and LTP History tracking tables
Migration script to create enhanced tracking tables for Strategy 1
"""

from app import create_app, db
from app.models.strategy_models import Strategy1Entry, Strategy1LTPHistory

def upgrade():
    """Create the new tracking tables"""
    app = create_app()
    
    with app.app_context():
        print("Creating Strategy1Entry and Strategy1LTPHistory tables...")
        
        # Create all tables
        db.create_all()
        
        print("✅ Strategy1Entry table created")
        print("✅ Strategy1LTPHistory table created")
        print("Migration completed successfully!")

def downgrade():
    """Drop the tracking tables (use with caution)"""
    app = create_app()
    
    with app.app_context():
        print("Dropping Strategy1Entry and Strategy1LTPHistory tables...")
        
        Strategy1LTPHistory.__table__.drop(db.engine, checkfirst=True)
        Strategy1Entry.__table__.drop(db.engine, checkfirst=True)
        
        print("Tables dropped successfully!")

if __name__ == "__main__":
    # Run upgrade
    upgrade()
