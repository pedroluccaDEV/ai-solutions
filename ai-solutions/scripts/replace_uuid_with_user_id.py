#!/usr/bin/env python3
"""
Script to replace UUID usage with user_id across all PostgreSQL tables.
Replaces gen_random_uuid() with SEQUENCE and ensures all foreign keys reference users.id.
"""

import os
import sys
from sqlmodel import Session, create_engine
from sqlalchemy import text
from dotenv import load_dotenv

# Add the server directory to the path to import models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def get_db_engine():
    """Get database engine from environment variables"""
    load_dotenv()
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Use default for testing
        database_url = "postgresql://postgres:root@localhost:5433/saphien"
    
    return create_engine(database_url)

def check_table_exists(session, table_name):
    """Check if a table exists in the database"""
    result = session.execute(text(f"""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = '{table_name}'
        )
    """))
    return result.fetchone()[0]

def get_column_info(session, table_name, column_name):
    """Get information about a specific column"""
    result = session.execute(text(f"""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = '{table_name}'
        AND column_name = '{column_name}'
    """))
    return result.fetchone()

def drop_foreign_key_constraints(engine):
    """Drop foreign key constraints that reference organizations table"""
    with Session(engine) as session:
        # Get all foreign key constraints referencing organizations
        result = session.execute(text("""
            SELECT conname, contype, conrelid::regclass as table_name
            FROM pg_constraint
            WHERE confrelid = 'organizations'::regclass
        """))
        constraints = result.fetchall()
        
        for conname, contype, table_name in constraints:
            if contype == 'f':  # Foreign key constraint
                session.execute(text(f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS {conname}"))
                print(f"Dropped foreign key constraint: {conname} from {table_name}")
        
        session.commit()
        print("Foreign key constraints dropped successfully")

def create_sequences(engine):
    """Create necessary sequences for tables"""
    with Session(engine) as session:
        # Create sequences for tables that need them
        sequences = [
            'organizations_id_seq',
            'projects_id_seq',
            'user_preferences_id_seq',
            'user_credits_id_seq'
        ]
        
        for seq_name in sequences:
            session.execute(text(f"""
                CREATE SEQUENCE IF NOT EXISTS {seq_name}
            """))
        
        session.commit()  # Commit to ensure sequences are created
        print("Sequences created successfully")

def create_mapping_tables(engine):
    """Create temporary mapping tables for UUID to bigint conversion"""
    with Session(engine) as session:
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS old_to_new_org_mapping (
                old_id uuid PRIMARY KEY,
                new_id bigint NOT NULL
            )
        """))
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS old_to_new_project_mapping (
                old_id uuid PRIMARY KEY,
                new_id bigint NOT NULL
            )
        """))
        print("Mapping tables created")

def drop_mapping_tables(engine):
    """Drop temporary mapping tables"""
    with Session(engine) as session:
        session.execute(text("DROP TABLE IF EXISTS old_to_new_org_mapping"))
        session.execute(text("DROP TABLE IF EXISTS old_to_new_project_mapping"))
        print("Mapping tables dropped")

def restructure_organizations_table(engine):
    """Restructure organizations table according to new schema"""
    with Session(engine) as session:
        if check_table_exists(session, 'organizations'):
            print("Restructuring organizations table...")
            
            # Create new organizations table with temporary name to avoid constraint conflicts
            session.execute(text("""
                CREATE TABLE organizations_new (
                    id bigint NOT NULL DEFAULT nextval('organizations_id_seq'::regclass),
                    user_id bigint NOT NULL,
                    name character varying(255) NOT NULL,
                    description text,
                    created_by timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
                    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT organizations_new_pkey PRIMARY KEY (id),
                    CONSTRAINT organizations_new_user_id_fkey FOREIGN KEY (user_id)
                        REFERENCES users (id) MATCH SIMPLE
                        ON UPDATE NO ACTION
                        ON DELETE NO ACTION
                )
            """))
            
            # Insert data from old table and populate mapping table
            result = session.execute(text("""
                SELECT id, created_by, name, description, created_at
                FROM organizations
            """))
            rows = result.fetchall()
            
            for row in rows:
                old_id = row[0]
                old_created_by = row[1]  # This is the user id who created the organization
                name = row[2]
                description = row[3]
                created_at = row[4]
                
                # Insert into new table - user_id gets the old created_by value,
                # created_by gets the created_at timestamp (as per new schema),
                # created_at remains the same
                new_id_result = session.execute(text("""
                    INSERT INTO organizations_new (user_id, name, description, created_by, created_at)
                    VALUES (:user_id, :name, :description, :created_by, :created_at)
                    RETURNING id
                """), {
                    'user_id': old_created_by,
                    'name': name,
                    'description': description,
                    'created_by': created_at,  # Set to timestamp
                    'created_at': created_at
                })
                new_id = new_id_result.fetchone()[0]
                
                # Store mapping from old UUID to new bigint
                session.execute(text("""
                    INSERT INTO old_to_new_org_mapping (old_id, new_id)
                    VALUES (:old_id, :new_id)
                """), {
                    'old_id': old_id,
                    'new_id': new_id
                })
            
            # Drop old table and rename new table
            session.execute(text("DROP TABLE organizations CASCADE"))
            session.execute(text("ALTER TABLE organizations_new RENAME TO organizations"))
            
            # Rename constraints to match original naming convention
            session.execute(text("""
                ALTER TABLE organizations
                RENAME CONSTRAINT organizations_new_pkey TO organizations_pkey
            """))
            session.execute(text("""
                ALTER TABLE organizations
                RENAME CONSTRAINT organizations_new_user_id_fkey TO organizations_user_id_fkey
            """))
            
            print("Organizations table restructured successfully")
        else:
            print("Organizations table doesn't exist")

def restructure_projects_table(engine):
    """Restructure projects table to use bigint instead of UUID"""
    with Session(engine) as session:
        if check_table_exists(session, 'projects'):
            print("Restructuring projects table...")
            
            # Create project mapping table if it doesn't exist
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS old_to_new_project_mapping (
                    old_id uuid PRIMARY KEY,
                    new_id bigint NOT NULL
                )
            """))
            session.commit()  # Commit to ensure mapping table exists
            
            # Backup old table
            session.execute(text("ALTER TABLE projects RENAME TO projects_old"))
            session.commit()
            
            # Create new projects table with bigint id
            session.execute(text("""
                CREATE TABLE projects (
                    id bigint NOT NULL DEFAULT nextval('projects_id_seq'::regclass),
                    name varchar NOT NULL,
                    description varchar,
                    organization_id bigint NOT NULL,
                    created_by int NOT NULL,
                    is_active boolean DEFAULT true,
                    created_at timestamp DEFAULT CURRENT_TIMESTAMP,
                    updated_at timestamp DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (id),
                    FOREIGN KEY (organization_id) REFERENCES organizations(id),
                    FOREIGN KEY (created_by) REFERENCES users(id)
                )
            """))
            session.commit()
            
            # Insert data from old table and populate mapping table
            result = session.execute(text("""
                SELECT id, name, description, organization_id, created_by, is_active, created_at, updated_at
                FROM projects_old
            """))
            rows = result.fetchall()
            
            for row in rows:
                old_id = row[0]
                name = row[1]
                description = row[2]
                old_org_id = row[3]  # UUID organization_id
                created_by = row[4]
                is_active = row[5]
                created_at = row[6]
                updated_at = row[7]
                
                # Get new organization ID from mapping
                org_mapping_result = session.execute(text("""
                    SELECT new_id FROM old_to_new_org_mapping WHERE old_id = :old_org_id
                """), {'old_org_id': old_org_id})
                org_mapping = org_mapping_result.fetchone()
                
                if org_mapping:
                    new_org_id = org_mapping[0]
                else:
                    print(f"Warning: No mapping found for organization_id {old_org_id}. Skipping project.")
                    continue
                
                # Insert into new table
                new_id_result = session.execute(text("""
                    INSERT INTO projects (name, description, organization_id, created_by, is_active, created_at, updated_at)
                    VALUES (:name, :description, :organization_id, :created_by, :is_active, :created_at, :updated_at)
                    RETURNING id
                """), {
                    'name': name,
                    'description': description,
                    'organization_id': new_org_id,
                    'created_by': created_by,
                    'is_active': is_active,
                    'created_at': created_at,
                    'updated_at': updated_at
                })
                new_id = new_id_result.fetchone()[0]
                
                # Store mapping from old UUID to new bigint
                session.execute(text("""
                    INSERT INTO old_to_new_project_mapping (old_id, new_id)
                    VALUES (:old_id, :new_id)
                """), {
                    'old_id': old_id,
                    'new_id': new_id
                })
            
            session.commit()  # Commit all inserts
            
            # Drop backup table
            session.execute(text("DROP TABLE projects_old CASCADE"))
            session.commit()
            
            print("Projects table restructured successfully")
        else:
            print("Projects table doesn't exist")

def restructure_project_members_table(engine):
    """Update project_members table to use bigint project_id"""
    with Session(engine) as session:
        if check_table_exists(session, 'project_members'):
            print("Updating project_members table...")
            
            # Check if project_id is UUID
            project_id_info = get_column_info(session, 'project_members', 'project_id')
            if project_id_info and project_id_info[1] == 'uuid':
                # First, create a temporary column to hold the new bigint values
                session.execute(text("""
                    ALTER TABLE project_members
                    ADD COLUMN temp_project_id bigint
                """))
                
                # Update the temporary column with mapped values
                session.execute(text("""
                    UPDATE project_members pm
                    SET temp_project_id = mapping.new_id
                    FROM old_to_new_project_mapping mapping
                    WHERE pm.project_id = mapping.old_id
                """))
                
                # Drop the old project_id column
                session.execute(text("""
                    ALTER TABLE project_members
                    DROP COLUMN project_id
                """))
                
                # Rename the temporary column to project_id
                session.execute(text("""
                    ALTER TABLE project_members
                    RENAME COLUMN temp_project_id TO project_id
                """))
                
                # Re-add foreign key constraint
                session.execute(text("""
                    ALTER TABLE project_members
                    ADD CONSTRAINT project_members_project_id_fkey
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                """))
                
                session.commit()
                print("Project_members table updated successfully")
            else:
                print("Project_members table already has correct structure")
        else:
            print("Project_members table doesn't exist")

def restructure_user_preferences_table(engine):
    """Restructure user_preferences table to use bigint instead of UUID"""
    with Session(engine) as session:
        if check_table_exists(session, 'user_preferences'):
            print("Restructuring user_preferences table...")
            
            # Backup old table
            session.execute(text("ALTER TABLE user_preferences RENAME TO user_preferences_old"))
            
            # Create new table with bigint id
            session.execute(text("""
                CREATE TABLE user_preferences (
                    id bigint NOT NULL DEFAULT nextval('user_preferences_id_seq'::regclass),
                    user_id int NOT NULL,
                    theme varchar DEFAULT 'light',
                    language varchar DEFAULT 'pt-BR',
                    email_notifications boolean DEFAULT true,
                    push_notifications boolean DEFAULT true,
                    auto_save boolean DEFAULT true,
                    auto_save_interval int DEFAULT 30,
                    created_at timestamp DEFAULT CURRENT_TIMESTAMP,
                    updated_at timestamp DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (id),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE (user_id)
                )
            """))
            
            # Copy data
            session.execute(text("""
                INSERT INTO user_preferences (user_id, theme, language, email_notifications, 
                                           push_notifications, auto_save, auto_save_interval, 
                                           created_at, updated_at)
                SELECT user_id, theme, language, email_notifications, 
                       push_notifications, auto_save, auto_save_interval, 
                       created_at, updated_at
                FROM user_preferences_old
            """))
            
            # Drop backup table
            session.execute(text("DROP TABLE user_preferences_old CASCADE"))
            
            print("User_preferences table restructured successfully")
        else:
            print("User_preferences table doesn't exist")

def restructure_user_credits_table(engine):
    """Update user_credits table to use user_id (int) instead of firebase_uid"""
    with Session(engine) as session:
        if check_table_exists(session, 'user_credits'):
            print("Updating user_credits table...")
            
            # Check if user_id references firebase_uid
            user_id_info = get_column_info(session, 'user_credits', 'user_id')
            if user_id_info and user_id_info[1] == 'character varying':
                # Backup old table
                session.execute(text("ALTER TABLE user_credits RENAME TO user_credits_old"))
                
                # Create new table with correct foreign key
                session.execute(text("""
                    CREATE TABLE user_credits (
                        id bigint NOT NULL DEFAULT nextval('user_credits_id_seq'::regclass),
                        user_id int NOT NULL,
                        subscription_credits int DEFAULT 0,
                        subscription_credits_used int DEFAULT 0,
                        recharge_credits int DEFAULT 0,
                        recharge_credits_used int DEFAULT 0,
                        last_monthly_reset timestamp,
                        created_at timestamp DEFAULT CURRENT_TIMESTAMP,
                        updated_at timestamp,
                        PRIMARY KEY (id),
                        FOREIGN KEY (user_id) REFERENCES users(id),
                        UNIQUE (user_id)
                    )
                """))
                
                # Copy data by mapping firebase_uid to user id
                session.execute(text("""
                    INSERT INTO user_credits (user_id, subscription_credits, subscription_credits_used,
                                           recharge_credits, recharge_credits_used, last_monthly_reset,
                                           created_at, updated_at)
                    SELECT u.id, uc.subscription_credits, uc.subscription_credits_used,
                           uc.recharge_credits, uc.recharge_credits_used, uc.last_monthly_reset,
                           uc.created_at, uc.updated_at
                    FROM user_credits_old uc
                    JOIN users u ON uc.user_id = u.firebase_uid
                """))
                
                # Drop backup table
                session.execute(text("DROP TABLE user_credits_old CASCADE"))
                
                print("User_credits table updated successfully")
            else:
                print("User_credits table already has correct structure")
        else:
            print("User_credits table doesn't exist")

def drop_unnecessary_tables(engine):
    """Drop tables that are no longer needed or use UUID"""
    with Session(engine) as session:
        tables_to_drop = [
            'organization_preferences',
            'integrations'
        ]
        
        for table_name in tables_to_drop:
            if check_table_exists(session, table_name):
                session.execute(text(f"DROP TABLE {table_name} CASCADE"))
                print(f"Dropped {table_name} table")
            else:
                print(f"{table_name} table doesn't exist")

def main():
    """Main function to execute all restructuring operations"""
    try:
        engine = get_db_engine()
        
        print("Starting UUID to user_id conversion...")
        
        # Execute operations in order
        drop_foreign_key_constraints(engine)  # Drop constraints first
        create_sequences(engine)
        create_mapping_tables(engine)
        restructure_organizations_table(engine)
        restructure_projects_table(engine)
        restructure_project_members_table(engine)
        restructure_user_preferences_table(engine)
        restructure_user_credits_table(engine)
        drop_unnecessary_tables(engine)
        drop_mapping_tables(engine)
        
        print("UUID to user_id conversion completed successfully!")
        
    except Exception as e:
        print(f"Error during database restructuring: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()