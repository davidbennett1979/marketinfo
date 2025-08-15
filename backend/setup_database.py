#!/usr/bin/env python3
"""
Database setup script for creating the watchlists table in Supabase.
"""

import os
import logging
from supabase import create_client

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_watchlists_table():
    """Create the watchlists table if it doesn't exist."""
    
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        logger.error("Missing Supabase credentials in environment variables")
        return False
    
    try:
        # Initialize Supabase client
        supabase = create_client(supabase_url, supabase_key)
        
        # SQL to create watchlists table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS public.watchlists (
            id BIGSERIAL PRIMARY KEY,
            user_id UUID NOT NULL,
            symbol VARCHAR(20) NOT NULL,
            symbol_type VARCHAR(10) NOT NULL DEFAULT 'stock',
            added_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(user_id, symbol)
        );
        
        -- Create indexes for better performance
        CREATE INDEX IF NOT EXISTS idx_watchlists_user_id ON public.watchlists(user_id);
        CREATE INDEX IF NOT EXISTS idx_watchlists_symbol ON public.watchlists(symbol);
        CREATE INDEX IF NOT EXISTS idx_watchlists_user_symbol ON public.watchlists(user_id, symbol);
        
        -- Enable Row Level Security
        ALTER TABLE public.watchlists ENABLE ROW LEVEL SECURITY;
        
        -- Create policy to allow users to only access their own watchlist items
        DROP POLICY IF EXISTS "Users can only access their own watchlist items" ON public.watchlists;
        CREATE POLICY "Users can only access their own watchlist items" ON public.watchlists
            FOR ALL USING (auth.uid() = user_id);
        
        -- Create trigger to update updated_at timestamp
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        DROP TRIGGER IF EXISTS update_watchlists_updated_at ON public.watchlists;
        CREATE TRIGGER update_watchlists_updated_at
            BEFORE UPDATE ON public.watchlists
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """
        
        # Execute the SQL
        result = supabase.rpc('exec_sql', {'sql': create_table_sql}).execute()
        
        logger.info("Successfully created watchlists table and related objects")
        return True
        
    except Exception as e:
        logger.error(f"Error creating watchlists table: {str(e)}")
        
        # Try alternative approach using direct SQL execution
        try:
            # Check if table exists by trying to select from it
            test_result = supabase.table('watchlists').select('id').limit(1).execute()
            logger.info("Watchlists table already exists")
            return True
            
        except Exception as e2:
            logger.error(f"Watchlists table does not exist and could not be created: {str(e2)}")
            
            # Print instructions for manual setup
            print("\n" + "="*60)
            print("MANUAL DATABASE SETUP REQUIRED")
            print("="*60)
            print("\nPlease execute the following SQL in your Supabase SQL editor:")
            print("\n" + create_table_sql)
            print("\n" + "="*60)
            
            return False

def check_table_exists():
    """Check if the watchlists table exists."""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        return False
    
    try:
        supabase = create_client(supabase_url, supabase_key)
        result = supabase.table('watchlists').select('id').limit(1).execute()
        logger.info("Watchlists table exists and is accessible")
        return True
    except Exception as e:
        logger.warning(f"Watchlists table check failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    print("Checking database setup...")
    
    if check_table_exists():
        print("✅ Watchlists table exists and is ready to use")
    else:
        print("❌ Watchlists table does not exist, attempting to create...")
        if setup_watchlists_table():
            print("✅ Database setup completed successfully")
        else:
            print("❌ Database setup failed - manual intervention required")