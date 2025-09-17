#!/usr/bin/env python3
"""
Database initialization script for DataWipe API.
This script creates the database tables and optionally seeds them with sample data.
"""

import asyncio
import sys
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Import our models and database configuration
from database import Base, engine, SQLALCHEMY_DATABASE_URL
from models.user import User
from models.wipe_log import WipeLog, WipeMethod, VerificationStatus


def create_tables():
    """Create all database tables"""
    try:
        print("🔧 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False


def drop_tables():
    """Drop all database tables (use with caution!)"""
    try:
        print("🗑️  Dropping all database tables...")
        Base.metadata.drop_all(bind=engine)
        print("✅ All tables dropped successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to drop tables: {e}")
        return False


def seed_sample_data():
    """Seed the database with sample data for testing"""
    try:
        print("🌱 Seeding database with sample data...")
        
        # Create a new session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # Check if data already exists
            existing_users = db.query(User).count()
            if existing_users > 0:
                print("⚠️  Database already contains data. Skipping seed.")
                return True
            
            # Create sample users
            users_data = [
                {
                    "name": "John Smith",
                    "org": "Acme Corporation",
                    "device_serial": "DEV001-ACME-2024"
                },
                {
                    "name": "Jane Doe",
                    "org": "Tech Solutions Inc",
                    "device_serial": "DEV002-TECH-2024"
                },
                {
                    "name": "Bob Johnson",
                    "org": "Secure Systems Ltd",
                    "device_serial": "DEV003-SEC-2024"
                },
                {
                    "name": "Alice Brown",
                    "org": "Data Corp",
                    "device_serial": "DEV004-DATA-2024"
                }
            ]
            
            created_users = []
            for user_data in users_data:
                user = User(**user_data)
                db.add(user)
                created_users.append(user)
            
            db.commit()
            
            # Refresh users to get their IDs
            for user in created_users:
                db.refresh(user)
            
            print(f"✅ Created {len(created_users)} sample users")
            
            # Create sample wipe logs
            wipe_logs_data = [
                {
                    "user_id": created_users[0].id,
                    "wipe_method": WipeMethod.SECURE_DELETE,
                    "start_time": datetime.utcnow() - timedelta(hours=2),
                    "end_time": datetime.utcnow() - timedelta(hours=1, 30),
                    "verification_status": VerificationStatus.VERIFIED,
                    "certificate_path": "/certificates/wipe_cert_001.pem"
                },
                {
                    "user_id": created_users[1].id,
                    "wipe_method": WipeMethod.CRYPTO_WIPE,
                    "start_time": datetime.utcnow() - timedelta(hours=1),
                    "end_time": datetime.utcnow() - timedelta(minutes=30),
                    "verification_status": VerificationStatus.PENDING,
                    "certificate_path": "/certificates/wipe_cert_002.pem"
                },
                {
                    "user_id": created_users[2].id,
                    "wipe_method": WipeMethod.OVERWRITE,
                    "start_time": datetime.utcnow() - timedelta(minutes=30),
                    "end_time": None,  # Still in progress
                    "verification_status": VerificationStatus.PENDING,
                    "certificate_path": None
                },
                {
                    "user_id": created_users[3].id,
                    "wipe_method": WipeMethod.PHYSICAL_DESTRUCTION,
                    "start_time": datetime.utcnow() - timedelta(days=1),
                    "end_time": datetime.utcnow() - timedelta(days=1) + timedelta(hours=2),
                    "verification_status": VerificationStatus.VERIFIED,
                    "certificate_path": "/certificates/wipe_cert_003.pem"
                }
            ]
            
            for wipe_log_data in wipe_logs_data:
                wipe_log = WipeLog(**wipe_log_data)
                db.add(wipe_log)
            
            db.commit()
            print(f"✅ Created {len(wipe_logs_data)} sample wipe logs")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Failed to seed sample data: {e}")
        return False


def verify_database():
    """Verify that the database is properly set up"""
    try:
        print("🔍 Verifying database setup...")
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # Check if tables exist and are accessible
            user_count = db.query(User).count()
            wipe_log_count = db.query(WipeLog).count()
            
            print(f"✅ Users table: {user_count} records")
            print(f"✅ Wipe logs table: {wipe_log_count} records")
            
            # Test a simple query
            recent_wipe_logs = db.query(WipeLog).order_by(WipeLog.created_at.desc()).limit(3).all()
            print(f"✅ Recent wipe logs: {len(recent_wipe_logs)} found")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False


def show_database_info():
    """Show information about the current database"""
    print("\n📊 Database Information:")
    print(f"   Database URL: {SQLALCHEMY_DATABASE_URL}")
    print(f"   Database file: {SQLALCHEMY_DATABASE_URL.replace('sqlite:///', '')}")
    
    try:
        import os
        db_file = SQLALCHEMY_DATABASE_URL.replace('sqlite:///', '')
        if os.path.exists(db_file):
            file_size = os.path.getsize(db_file)
            print(f"   Database size: {file_size} bytes")
        else:
            print("   Database file: Not found")
    except Exception as e:
        print(f"   Error getting file info: {e}")


def main():
    """Main initialization function"""
    print("🚀 DataWipe Database Initialization")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "create":
            success = create_tables()
            if success:
                print("\n🎉 Database tables created successfully!")
            else:
                sys.exit(1)
                
        elif command == "drop":
            confirm = input("⚠️  Are you sure you want to drop all tables? (yes/no): ")
            if confirm.lower() == "yes":
                success = drop_tables()
                if success:
                    print("\n🗑️  All tables dropped successfully!")
                else:
                    sys.exit(1)
            else:
                print("❌ Operation cancelled")
                
        elif command == "seed":
            success = create_tables() and seed_sample_data()
            if success:
                print("\n🌱 Database seeded with sample data!")
            else:
                sys.exit(1)
                
        elif command == "reset":
            print("🔄 Resetting database...")
            drop_tables()
            success = create_tables() and seed_sample_data()
            if success:
                print("\n🔄 Database reset and seeded successfully!")
            else:
                sys.exit(1)
                
        elif command == "verify":
            success = verify_database()
            if success:
                print("\n✅ Database verification successful!")
            else:
                sys.exit(1)
                
        else:
            print(f"❌ Unknown command: {command}")
            print_usage()
            sys.exit(1)
    else:
        # Default: create tables and seed data
        print("🔧 Creating database tables...")
        success = create_tables()
        
        if success:
            print("\n🌱 Seeding with sample data...")
            seed_success = seed_sample_data()
            
            if seed_success:
                print("\n🔍 Verifying setup...")
                verify_database()
                
                print("\n🎉 Database initialization completed successfully!")
                show_database_info()
            else:
                print("\n⚠️  Tables created but seeding failed")
        else:
            print("\n❌ Database initialization failed")
            sys.exit(1)


def print_usage():
    """Print usage information"""
    print("\n📖 Usage:")
    print("   python init_db.py              # Create tables and seed data")
    print("   python init_db.py create       # Create tables only")
    print("   python init_db.py seed         # Create tables and seed data")
    print("   python init_db.py reset        # Drop, create, and seed")
    print("   python init_db.py drop         # Drop all tables")
    print("   python init_db.py verify       # Verify database setup")


if __name__ == "__main__":
    main()
