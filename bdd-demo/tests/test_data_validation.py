"""Pytest tests for data validation with rich reporting."""

import pytest
import pandas as pd
from app.db_utils import get_db_manager
from app.ge_checks import DataQualityChecker


class TestDataValidation:
    """Test class for data validation scenarios."""
    
    @pytest.fixture(scope="class")
    def db_manager(self):
        """Database manager fixture."""
        db = get_db_manager()
        db.connect()
        yield db
        db.disconnect()
    
    @pytest.fixture(scope="class")
    def quality_checker(self):
        """Data quality checker fixture."""
        return DataQualityChecker()
    
    @pytest.mark.database
    def test_database_connection(self, db_manager):
        """Test database connection is working."""
        assert db_manager.is_connected(), "Database should be connected"
    
    @pytest.mark.database
    def test_clients_table_exists(self, db_manager):
        """Test that clients table exists and has data."""
        table_info = db_manager.get_table_info('clients')
        assert table_info is not None, "Clients table should exist"
        assert table_info['row_count'] > 0, "Clients table should have data"
    
    @pytest.mark.database
    @pytest.mark.parametrize("client_name,expected_min_revenue", [
        ("Client A", 100000),
        ("Client B", 200000),
        ("Client C", 50000),
    ])
    def test_client_revenue_validation(self, db_manager, client_name, expected_min_revenue):
        """Test client revenue validation with parameterized inputs."""
        query = f"SELECT revenue FROM clients WHERE client_name = '{client_name}'"
        result = db_manager.execute_query(query)
        
        assert result is not None, f"Should find data for {client_name}"
        assert len(result) > 0, f"Should have revenue data for {client_name}"
        
        revenue = result[0]['revenue']
        assert revenue is not None, f"Revenue should not be null for {client_name}"
        assert revenue >= expected_min_revenue, f"Revenue for {client_name} should be at least ${expected_min_revenue:,}"
        assert revenue > 0, f"Revenue for {client_name} should be positive"
    
    @pytest.mark.database
    def test_data_quality_expectations(self, quality_checker):
        """Test data quality using Great Expectations."""
        # Validate clients table
        result = quality_checker.validate_database_table('clients', expected_count=5)
        
        assert result['success'], f"Data quality validation should pass: {result.get('error', '')}"
        assert result['statistics']['success_percent'] == 100.0, "All expectations should pass"
    
    @pytest.mark.api
    def test_api_data_quality(self, quality_checker):
        """Test API data quality validation."""
        # Mock API data
        api_data = {
            'data': [
                {'client_id': 1, 'client_name': 'Test Client', 'revenue': 150000.50},
                {'client_id': 2, 'client_name': 'Another Client', 'revenue': 275000.75}
            ]
        }
        
        result = quality_checker.validate_api_data(api_data)
        
        assert result['success'], f"API data validation should pass: {result.get('error', '')}"
        assert result['statistics']['evaluated_expectations'] > 0, "Should have evaluated some expectations"
    
    @pytest.mark.slow
    def test_large_dataset_validation(self, quality_checker):
        """Test validation with larger dataset (marked as slow)."""
        # Generate larger mock dataset
        large_data = {
            'data': [
                {'client_id': i, 'client_name': f'Client {i}', 'revenue': 50000 + (i * 1000)}
                for i in range(1, 101)  # 100 clients
            ]
        }
        
        result = quality_checker.validate_api_data(large_data)
        
        assert result['success'], "Large dataset validation should pass"
        assert result['statistics']['evaluated_expectations'] > 0, "Should validate multiple expectations"
    
    @pytest.mark.parametrize("test_data,expected_success", [
        ({'data': [{'revenue': 100}]}, True),  # Valid positive revenue
        ({'data': [{'revenue': -100}]}, False),  # Invalid negative revenue
        ({'data': [{'revenue': None}]}, False),  # Invalid null revenue
        ({'data': [{'revenue': 2000000}]}, False),  # Invalid too high revenue
    ])
    def test_revenue_validation_scenarios(self, quality_checker, test_data, expected_success):
        """Test various revenue validation scenarios."""
        result = quality_checker.validate_api_data(test_data)
        
        if expected_success:
            assert result['success'], f"Validation should pass for valid data: {test_data}"
        else:
            # For invalid data, we expect some expectations to fail
            assert result['statistics']['unsuccessful_expectations'] > 0, f"Should have validation failures for invalid data: {test_data}"


class TestDataIntegrity:
    """Test class for data integrity checks."""
    
    @pytest.mark.integration
    def test_csv_to_database_integrity(self):
        """Test data integrity from CSV to database."""
        # Read CSV file
        csv_file = 'data/sample_feed.csv'
        df = pd.read_csv(csv_file)
        csv_count = len(df)
        
        # Check database count
        db = get_db_manager()
        db.connect()
        table_info = db.get_table_info('clients')
        db_count = table_info['row_count'] if table_info else 0
        db.disconnect()
        
        assert csv_count == db_count, f"CSV count ({csv_count}) should match DB count ({db_count})"
    
    @pytest.mark.integration
    def test_data_consistency_across_sources(self):
        """Test data consistency across different sources."""
        db = get_db_manager()
        db.connect()
        
        # Get data from database
        db_data = db.execute_query("SELECT client_name, revenue FROM clients ORDER BY client_id")
        
        # Verify data consistency
        assert len(db_data) > 0, "Should have data in database"
        
        for record in db_data:
            assert record['client_name'] is not None, "Client name should not be null"
            assert record['revenue'] is not None, "Revenue should not be null"
            assert isinstance(record['revenue'], (int, float)), "Revenue should be numeric"
            assert record['revenue'] > 0, "Revenue should be positive"
        
        db.disconnect()


# Pytest hooks for enhanced reporting
def pytest_html_report_title(report):
    """Customize HTML report title."""
    report.title = "BDD Demo - Data Validation Test Report"


def pytest_html_results_summary(prefix, summary, postfix):
    """Customize HTML report summary."""
    prefix.extend([
        "<h2>BDD Demo Test Execution Summary</h2>",
        "<p>This report shows the results of data validation tests including database integrity, API data quality, and parameterized test scenarios.</p>"
    ])


def pytest_configure(config):
    """Configure pytest with custom markers and metadata."""
    config.addinivalue_line("markers", "parametrize: Parameterized test scenarios")
    
    # Add metadata for HTML report
    if hasattr(config, '_metadata'):
        config._metadata['Project'] = 'BDD Demo - Data Validation'
        config._metadata['Test Environment'] = 'Local Development'
        config._metadata['Database'] = 'SQLite'
        config._metadata['Python Version'] = '3.10+'
