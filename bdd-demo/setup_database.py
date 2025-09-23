#!/usr/bin/env python3
"""Setup script to initialize the database with sample data."""

import os
import sys
import logging
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db_utils import get_db_manager
from app.utils import setup_logging, ensure_directory_exists

def main():
    """Initialize the database with sample data."""
    logger = setup_logging()
    logger.info("Starting database setup...")
    
    try:
        # Ensure data directory exists
        ensure_directory_exists('data')
        
        # Get database manager
        db = get_db_manager()
        
        # Connect to database
        if not db.connect():
            logger.error("Failed to connect to database")
            return False
        
        logger.info("Connected to database successfully")
        
        # Setup sample data
        logger.info("Setting up sample data...")
        success = db.setup_sample_data()
        
        if success:
            logger.info("Sample data setup completed successfully")
            
            # Verify the data was loaded
            count = db.get_table_count('clients')
            logger.info(f"Clients table now has {count} records")
            
            # Show sample data
            sample_query = "SELECT * FROM clients LIMIT 3"
            sample_data = db.execute_query(sample_query)
            
            if sample_data:
                logger.info("Sample data preview:")
                for row in sample_data:
                    logger.info(f"  Client: {row['client_name']}, Revenue: ${row['revenue']:,.2f}")
            
            return True
        else:
            logger.error("Failed to setup sample data")
            return False
            
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        return False
    
    finally:
        if 'db' in locals():
            db.disconnect()

if __name__ == "__main__":
    success = main()
    if success:
        print("✅ Database setup completed successfully!")
        sys.exit(0)
    else:
        print("❌ Database setup failed!")
        sys.exit(1)
