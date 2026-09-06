"""
Script to migrate from SQLite to PostgreSQL
Usage: python migrate_to_postgresql.py
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# SQLite database URL
SQLITE_URL = 'sqlite:///delivery_dz.db'

# PostgreSQL database URL (update with your credentials)
POSTGRESQL_URL = 'postgresql://postgres:toor@localhost/delivery_dz'


def migrate_database():
    """Migrate data from SQLite to PostgreSQL"""
    
    print("🔄 Starting migration from SQLite to PostgreSQL...")
    
    # Create engines
    sqlite_engine = create_engine(SQLITE_URL)
    postgresql_engine = create_engine(POSTGRESQL_URL)
    
    # Create sessions
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    PostgreSQLSession = sessionmaker(bind=postgresql_engine)
    
    sqlite_session = SQLiteSession()
    postgresql_session = PostgreSQLSession()
    
    # Import models
    from models import (
        db, User, Restaurant, MenuItem, Order, OrderItem,
        RestaurantReview, DriverReview, Notification, Wallet, Transaction
    )
    
    # Create all tables in PostgreSQL
    print("📋 Creating tables in PostgreSQL...")
    db.metadata.create_all(postgresql_engine)
    
    # Migrate tables in order (respecting foreign keys)
    tables_to_migrate = [
        ('Users', User),
        ('Restaurants', Restaurant),
        ('MenuItems', MenuItem),
        ('Orders', Order),
        ('OrderItems', OrderItem),
        ('RestaurantReviews', RestaurantReview),
        ('DriverReviews', DriverReview),
        ('Notifications', Notification),
        ('Wallets', Wallet),
        ('Transactions', Transaction),
    ]
    
    for table_name, model in tables_to_migrate:
        print(f"📊 Migrating {table_name}...")
        
        # Get all records from SQLite
        records = sqlite_session.query(model).all()
        
        if records:
            # Add to PostgreSQL
            for record in records:
                # Create new instance without id (let PostgreSQL auto-generate)
                postgresql_session.merge(record)
            
            postgresql_session.commit()
            print(f"   ✅ Migrated {len(records)} records from {table_name}")
        else:
            print(f"   ⚠️ No records found in {table_name}")
    
    # Close sessions
    sqlite_session.close()
    postgresql_session.close()
    
    print("\n✅ Migration completed successfully!")
    print("📝 Next steps:")
    print("   1. Update .env file with PostgreSQL URL")
    print("   2. Restart your application")
    print("   3. Test everything works")
    print("   4. Backup SQLite file: cp delivery_dz.db delivery_dz.db.backup")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("   SQLite → PostgreSQL Migration Tool")
    print("="*60)
    
    # Confirm
    print("\n⚠️  WARNING: This will copy ALL data from SQLite to PostgreSQL")
    print("   Make sure:")
    print("   1. PostgreSQL is installed and running")
    print("   2. Database 'delivery_dz' exists in PostgreSQL")
    print("   3. You have a backup of your SQLite database")
    
    confirm = input("\n   Continue? (yes/no): ")
    
    if confirm.lower() == 'yes':
        try:
            migrate_database()
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            print("   Please fix the error and try again")
    else:
        print("\n❌ Migration cancelled")