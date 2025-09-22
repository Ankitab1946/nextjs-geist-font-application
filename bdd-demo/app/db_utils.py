"""Database utilities for SQLite and SQL Server connections."""

import sqlite3
import pandas as pd
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from app.config import Config
from app.utils import ensure_directory_exists

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database manager supporting both SQLite and SQL Server."""
    
    def __init__(self):
        self.config = Config()
        self.connection = None
        
    def connect(self) -> bool:
        """Establish database connection based on configuration."""
        try:
            if self.config.USE_SQL_SERVER:
                return self._connect_sql_server()
            else:
                return self._connect_sqlite()
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def _connect_sqlite(self) -> bool:
        """Connect to SQLite database."""
        try:
            # Ensure data directory exists
            db_path = Path(self.config.SQLITE_DB_PATH)
            ensure_directory_exists(str(db_path.parent))
            
            self.connection = sqlite3.connect(str(db_path))
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
            logger.info(f"Connected to SQLite database: {db_path}")
            return True
        except Exception as e:
            logger.error(f"SQLite connection failed: {e}")
            return False
    
    def _connect_sql_server(self) -> bool:
        """Connect to SQL Server database."""
        try:
            import pyodbc
            self.connection = pyodbc.connect(self.config.SQL_SERVER_CONNECTION)
            logger.info("Connected to SQL Server database")
            return True
        except ImportError:
            logger.error("pyodbc not installed. Cannot connect to SQL Server.")
            return False
        except Exception as e:
            logger.error(f"SQL Server connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Database connection closed")
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> Optional[List[Dict]]:
        """Execute a SELECT query and return results."""
        try:
            if not self.connection:
                if not self.connect():
                    return None
            
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Convert results to list of dictionaries
            columns = [description[0] for description in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return None
    
    def execute_non_query(self, query: str, params: Optional[tuple] = None) -> bool:
        """Execute INSERT, UPDATE, or DELETE query."""
        try:
            if not self.connection:
                if not self.connect():
                    return False
            
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            self.connection.commit()
            logger.info(f"Query executed successfully. Rows affected: {cursor.rowcount}")
            return True
        except Exception as e:
            logger.error(f"Non-query execution failed: {e}")
            return False
    
    def load_csv_to_table(self, csv_path: str, table_name: str, if_exists: str = 'replace') -> bool:
        """Load CSV data into database table."""
        try:
            # Read CSV file
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded CSV with {len(df)} rows and {len(df.columns)} columns")
            
            if not self.connection:
                if not self.connect():
                    return False
            
            # Load data to database
            if self.config.USE_SQL_SERVER:
                # For SQL Server, we need to use a different approach
                return self._load_df_to_sql_server(df, table_name, if_exists)
            else:
                # For SQLite, use pandas to_sql
                df.to_sql(table_name, self.connection, if_exists=if_exists, index=False)
                logger.info(f"Data loaded to table '{table_name}' successfully")
                return True
                
        except Exception as e:
            logger.error(f"CSV loading failed: {e}")
            return False
    
    def _load_df_to_sql_server(self, df: pd.DataFrame, table_name: str, if_exists: str) -> bool:
        """Load DataFrame to SQL Server table."""
        try:
            # This is a simplified implementation
            # In production, you might want to use bulk insert methods
            
            if if_exists == 'replace':
                # Drop table if exists
                drop_query = f"DROP TABLE IF EXISTS {table_name}"
                self.execute_non_query(drop_query)
            
            # Create table based on DataFrame structure
            create_query = self._generate_create_table_query(df, table_name)
            if not self.execute_non_query(create_query):
                return False
            
            # Insert data row by row (not efficient for large datasets)
            for _, row in df.iterrows():
                placeholders = ', '.join(['?' for _ in range(len(row))])
                insert_query = f"INSERT INTO {table_name} VALUES ({placeholders})"
                if not self.execute_non_query(insert_query, tuple(row)):
                    return False
            
            logger.info(f"Data loaded to SQL Server table '{table_name}' successfully")
            return True
            
        except Exception as e:
            logger.error(f"SQL Server data loading failed: {e}")
            return False
    
    def _generate_create_table_query(self, df: pd.DataFrame, table_name: str) -> str:
        """Generate CREATE TABLE query based on DataFrame structure."""
        columns = []
        for col_name, dtype in df.dtypes.items():
            if dtype == 'object':
                sql_type = 'VARCHAR(255)'
            elif dtype == 'int64':
                sql_type = 'INTEGER'
            elif dtype == 'float64':
                sql_type = 'FLOAT'
            elif dtype == 'bool':
                sql_type = 'BOOLEAN'
            else:
                sql_type = 'VARCHAR(255)'  # Default
            
            columns.append(f"{col_name} {sql_type}")
        
        return f"CREATE TABLE {table_name} ({', '.join(columns)})"
    
    def get_table_count(self, table_name: str) -> Optional[int]:
        """Get row count for a table."""
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = self.execute_query(query)
        
        if result and len(result) > 0:
            return result[0]['count']
        return None
    
    def get_table_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Get table information including column details."""
        try:
            if self.config.USE_SQL_SERVER:
                query = """
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    IS_NULLABLE,
                    CHARACTER_MAXIMUM_LENGTH
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = ?
                """
                columns_info = self.execute_query(query, (table_name,))
            else:
                # SQLite
                query = f"PRAGMA table_info({table_name})"
                columns_info = self.execute_query(query)
            
            row_count = self.get_table_count(table_name)
            
            return {
                'table_name': table_name,
                'row_count': row_count,
                'columns': columns_info
            }
            
        except Exception as e:
            logger.error(f"Failed to get table info for {table_name}: {e}")
            return None
    
    def setup_sample_data(self) -> bool:
        """Set up sample data for testing."""
        try:
            # Create sample data
            sample_data = {
                'client_id': [1, 2, 3, 4, 5],
                'client_name': ['Client A', 'Client B', 'Client C', 'Client D', 'Client E'],
                'revenue': [150000.50, 275000.75, 89000.25, 420000.00, 195000.30],
                'region': ['North', 'South', 'East', 'West', 'Central'],
                'active': [True, True, False, True, True]
            }
            
            df = pd.DataFrame(sample_data)
            
            # Save as CSV for testing
            csv_path = 'data/sample_feed.csv'
            ensure_directory_exists('data')
            df.to_csv(csv_path, index=False)
            logger.info(f"Sample CSV created: {csv_path}")
            
            # Load to database
            success = self.load_csv_to_table(csv_path, 'clients')
            if success:
                logger.info("Sample data loaded to database successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to setup sample data: {e}")
            return False

# Convenience functions for easy access
def get_db_manager() -> DatabaseManager:
    """Get a database manager instance."""
    return DatabaseManager()

def quick_query(query: str, params: Optional[tuple] = None) -> Optional[List[Dict]]:
    """Execute a quick query and return results."""
    db = get_db_manager()
    try:
        return db.execute_query(query, params)
    finally:
        db.disconnect()

def quick_count(table_name: str) -> Optional[int]:
    """Get quick row count for a table."""
    db = get_db_manager()
    try:
        return db.get_table_count(table_name)
    finally:
        db.disconnect()
