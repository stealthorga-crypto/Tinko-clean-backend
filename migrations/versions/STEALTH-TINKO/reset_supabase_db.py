#!/usr/bin/env python3
"""
Reset Supabase database by dropping all existing tables.
Run this before running migrations if you want a fresh start.
"""

import os
from sqlalchemy import create_engine, text

# Load environment variables
from app.db import SQLALCHEMY_DATABASE_URL

def reset_database():
    """Drop all tables in the database"""
    print("🔄 Resetting Supabase database...")

    try:
        engine = create_engine(SQLALCHEMY_DATABASE_URL)

        # Connect and get all table names
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename;
            """))

            tables = [row[0] for row in result.fetchall()]

            if not tables:
                print("✅ No tables to drop")
                return True

            print(f"Found {len(tables)} tables to drop:", tables)

            # Drop all tables with CASCADE to handle dependencies
            for table in tables:
                try:
                    print(f"Dropping table: {table}")
                    conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE;'))
                    conn.commit()
                except Exception as e:
                    print(f"⚠️  Could not drop {table}: {e}")
                    continue

            print("✅ Database reset complete")
            return True

    except Exception as e:
        print(f"❌ Database reset failed: {e}")
        return False

if __name__ == "__main__":
    if reset_database():
        print("\n🚀 Now you can run: alembic upgrade head")
        print("This will create a fresh schema from the migrations.")
    else:
        print("\n❌ Reset failed. Please check your database connection.")
