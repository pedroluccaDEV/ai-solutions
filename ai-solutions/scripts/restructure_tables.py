#!/usr/bin/env python3
"""
Script to restructure database tables according to new requirements:
1. organizations table adjustments
2. Delete organization_users and organization_preferences tables
3. invites table adjustments
4. project_members table adjustments
"""

import os
import sys
from sqlmodel import Session, create_engine
from sqlalchemy import text

# Add the server directory to the path to import models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def get_db_engine():
    """Get database engine from environment variables"""
    from dotenv import load_dotenv
    load_dotenv()
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Use default for testing
        database_url = "postgresql://postgres:root@localhost:5433/saphien"
    
    return create_engine(database_url)

def restructure_organizations_table(engine):
    """Restructure organizations table"""
    with Session(engine) as session:
        # Check if organizations table exists and has the current structure
        result = session.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'organizations'
            AND column_name = 'id'
        """))
        current_id_type = result.fetchone()
        
        if current_id_type and current_id_type[1] == 'uuid':
            print("Altering organizations table...")
            
            # Drop and recreate the table with new schema
            # First, backup the old table by renaming
            session.execute(text("ALTER TABLE organizations RENAME TO organizations_old"))
            
            # Create new organizations table with bigint id
            session.execute(text("""
                CREATE TABLE organizations (
                    id bigint NOT NULL DEFAULT nextval('organizationuser_id_seq'::regclass),
                    name varchar NOT NULL,
                    description varchar,
                    created_by bigint NOT NULL,
                    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (id)
                )
            """))
            
            # Copy data from old table to new table
            # Since id values change, we cannot preserve foreign keys, so organization_id in other tables will be set to NULL
            session.execute(text("""
                INSERT INTO organizations (name, description, created_by, created_at)
                SELECT name, description, created_by, created_at
                FROM organizations_old
            """))
            
            # Drop the backup table with CASCADE to handle dependent objects
            session.execute(text("DROP TABLE organizations_old CASCADE"))
            
            # Recreate indexes
            session.execute(text("CREATE INDEX ix_organizations_id ON organizations (id)"))
            
            # Verify the new structure
            result = session.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'organizations'
                AND column_name = 'id'
            """))
            new_id_type = result.fetchone()
            if new_id_type and new_id_type[1] == 'bigint':
                print("Organizations table restructured successfully - id is now bigint")
            else:
                print(f"WARNING: Organizations table restructuring may have failed. Current id type: {new_id_type[1] if new_id_type else 'unknown'}")
        else:
            print(f"Organizations table already has the correct structure or doesn't exist. Current id type: {current_id_type[1] if current_id_type else 'unknown'}")

def delete_tables(engine):
    """Delete organization_users and organization_preferences tables"""
    with Session(engine) as session:
        # Check and delete organization_users table
        session.execute(text("""
            DROP TABLE IF EXISTS organization_users CASCADE
        """))
        print("Deleted organization_users table if it existed")
        
        # Check and delete organization_preferences table
        session.execute(text("""
            DROP TABLE IF EXISTS organization_preferences CASCADE
        """))
        print("Deleted organization_preferences table if it existed")

def restructure_invites_table(engine):
    """Restructure invites table"""
    with Session(engine) as session:
        # Check if organization_id column exists and is UUID
        result = session.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'invites'
            AND column_name = 'organization_id'
        """))
        org_id_column = result.fetchone()
        
        if org_id_column and org_id_column[1] == 'uuid':
            print("Altering invites table...")
            
            # First, drop the foreign key constraint if it exists
            session.execute(text("""
                ALTER TABLE invites DROP CONSTRAINT IF EXISTS invites_organization_id_fkey
            """))
            
            # Set organization_id to NULL for all rows since we cannot map UUID to bigint
            session.execute(text("""
                UPDATE invites SET organization_id = NULL
            """))

            # Drop the organization_id column and recreate it with correct type
            session.execute(text("""
                ALTER TABLE invites DROP COLUMN organization_id
            """))

            # Add new organization_id column as bigint nullable
            session.execute(text("""
                ALTER TABLE invites ADD COLUMN organization_id bigint
            """))
            
            # Check if organizations table has bigint id before adding foreign key
            result = session.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'organizations'
                AND column_name = 'id'
            """))
            org_id_type = result.fetchone()
            if org_id_type and org_id_type[1] == 'bigint':
                # Recreate foreign key constraint to organizations table
                session.execute(text("""
                    ALTER TABLE invites
                    ADD CONSTRAINT invites_organization_id_fkey
                    FOREIGN KEY (organization_id) REFERENCES organizations(id)
                """))
                print("Foreign key constraint added to invites table")
            else:
                print(f"Organizations id type is {org_id_type[1] if org_id_type else 'unknown'}, skipping foreign key addition")
            
            print("Invites table restructured successfully")
        else:
            print("Invites table organization_id column already has correct type or doesn't exist")

def restructure_project_members_table(engine):
    """Restructure project_members table"""
    with Session(engine) as session:
        # Check if project_members table exists
        result = session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'project_members'
            )
        """))
        table_exists = result.fetchone()[0]
        
        if table_exists:
            print("Altering project_members table...")
            
            # Add status column if it doesn't exist
            session.execute(text("""
                ALTER TABLE project_members 
                ADD COLUMN IF NOT EXISTS status varchar DEFAULT 'pending'
            """))
            
            # Note: project_id column is required and should not be removed
            # It is a foreign key to projects table
            
            print("Project_members table restructured successfully")
        else:
            print("Project_members table doesn't exist")

def main():
    """Main function to execute all restructuring operations"""
    try:
        engine = get_db_engine()
        
        print("Starting database restructuring...")
        
        # Execute operations in order
        restructure_organizations_table(engine)
        delete_tables(engine)
        restructure_invites_table(engine)
        restructure_project_members_table(engine)
        
        print("Database restructuring completed successfully!")
        
    except Exception as e:
        print(f"Error during database restructuring: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()