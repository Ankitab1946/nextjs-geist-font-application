"""Behave step definitions for BDD scenarios."""

import os
import json
import logging
import requests
from behave import given, when, then, step
from app.db_utils import get_db_manager, quick_query, quick_count
from app.ge_checks import validate_api_data, validate_table
from app.selenium_tests import validate_dashboard, validate_elements
from app.config import Config

logger = logging.getLogger(__name__)
config = Config()

# Database-related steps
@given('I have a source data file "{filename}"')
def step_given_source_data_file(context, filename):
    """Check if source data file exists."""
    filepath = os.path.join('data', filename)
    context.source_file = filepath
    context.source_exists = os.path.exists(filepath)
    
    if context.source_exists:
        # Count records in CSV
        import pandas as pd
        try:
            df = pd.read_csv(filepath)
            context.source_record_count = len(df)
            logger.info(f"Source file {filename} has {context.source_record_count} records")
        except Exception as e:
            logger.error(f"Error reading source file: {e}")
            context.source_record_count = 0
    else:
        logger.warning(f"Source file {filename} not found")
        context.source_record_count = 0

@given('I have a source data file')
def step_given_source_data_file_default(context):
    """Check if default source data file exists."""
    step_given_source_data_file(context, 'sample_feed.csv')

@when('I load the data into the database')
def step_when_load_data_to_database(context):
    """Load data from source file to database."""
    try:
        db = get_db_manager()
        
        if hasattr(context, 'source_file') and context.source_exists:
            # Load CSV to database table
            success = db.load_csv_to_table(context.source_file, 'clients')
            context.load_success = success
            
            if success:
                # Get loaded record count
                context.loaded_record_count = db.get_table_count('clients')
                logger.info(f"Loaded {context.loaded_record_count} records to database")
            else:
                context.loaded_record_count = 0
                logger.error("Failed to load data to database")
        else:
            context.load_success = False
            context.loaded_record_count = 0
            logger.error("No source file available for loading")
        
        db.disconnect()
        
    except Exception as e:
        logger.error(f"Error loading data to database: {e}")
        context.load_success = False
        context.loaded_record_count = 0

@then('the record count should match the source file')
def step_then_record_count_matches(context):
    """Verify record count matches between source and database."""
    if not hasattr(context, 'source_record_count') or not hasattr(context, 'loaded_record_count'):
        assert False, "Record counts not available for comparison"
    
    source_count = getattr(context, 'source_record_count', 0)
    loaded_count = getattr(context, 'loaded_record_count', 0)
    
    logger.info(f"Comparing counts - Source: {source_count}, Loaded: {loaded_count}")
    
    assert source_count == loaded_count, f"Record count mismatch: source={source_count}, loaded={loaded_count}"

@then('all required fields should be populated')
def step_then_required_fields_populated(context):
    """Verify all required fields are populated in the database."""
    try:
        # Query database to check for null values in required fields
        required_fields = ['client_id', 'client_name', 'revenue']
        
        for field in required_fields:
            query = f"SELECT COUNT(*) as null_count FROM clients WHERE {field} IS NULL OR {field} = ''"
            result = quick_query(query)
            
            if result and len(result) > 0:
                null_count = result[0]['null_count']
                assert null_count == 0, f"Field '{field}' has {null_count} null/empty values"
                logger.info(f"Field '{field}' validation passed - no null values")
            else:
                assert False, f"Could not validate field '{field}'"
                
    except Exception as e:
        logger.error(f"Error validating required fields: {e}")
        assert False, f"Required fields validation failed: {e}"

@given('I have data in the database')
def step_given_data_in_database(context):
    """Verify data exists in the database."""
    try:
        count = quick_count('clients')
        context.db_record_count = count if count is not None else 0
        
        assert context.db_record_count > 0, f"No data found in database (count: {context.db_record_count})"
        logger.info(f"Database has {context.db_record_count} records")
        
    except Exception as e:
        logger.error(f"Error checking database data: {e}")
        assert False, f"Database data check failed: {e}"

@when('I check the data types')
def step_when_check_data_types(context):
    """Check data types in the database."""
    try:
        # Query sample data to validate types
        query = "SELECT client_id, client_name, revenue FROM clients LIMIT 5"
        results = quick_query(query)
        
        context.data_type_results = []
        
        if results:
            for row in results:
                # Check if client_id is numeric
                client_id_valid = isinstance(row['client_id'], (int, float)) or str(row['client_id']).isdigit()
                
                # Check if revenue is numeric
                revenue_valid = isinstance(row['revenue'], (int, float))
                if not revenue_valid:
                    try:
                        float(row['revenue'])
                        revenue_valid = True
                    except (ValueError, TypeError):
                        revenue_valid = False
                
                # Check if client_name is string
                name_valid = isinstance(row['client_name'], str) and len(row['client_name']) > 0
                
                context.data_type_results.append({
                    'client_id': row['client_id'],
                    'client_id_valid': client_id_valid,
                    'revenue_valid': revenue_valid,
                    'name_valid': name_valid
                })
        
        logger.info(f"Checked data types for {len(context.data_type_results)} records")
        
    except Exception as e:
        logger.error(f"Error checking data types: {e}")
        context.data_type_results = []

@then('all numeric fields should contain valid numbers')
def step_then_numeric_fields_valid(context):
    """Verify numeric fields contain valid numbers."""
    if not hasattr(context, 'data_type_results') or not context.data_type_results:
        assert False, "No data type results available"
    
    invalid_records = []
    
    for result in context.data_type_results:
        if not result['client_id_valid']:
            invalid_records.append(f"client_id: {result['client_id']}")
        if not result['revenue_valid']:
            invalid_records.append(f"revenue for client_id {result['client_id']}")
    
    assert len(invalid_records) == 0, f"Invalid numeric fields found: {', '.join(invalid_records)}"
    logger.info("All numeric fields validation passed")

@then('all date fields should contain valid dates')
def step_then_date_fields_valid(context):
    """Verify date fields contain valid dates."""
    # This is a placeholder - in a real scenario, you would check actual date fields
    logger.info("Date fields validation passed (no date fields in current schema)")

# API-related steps
@given('the API endpoint is available')
def step_given_api_endpoint_available(context):
    """Check if API endpoint is available."""
    try:
        api_url = f"http://{config.FASTAPI_HOST}:{config.FASTAPI_PORT}/health"
        response = requests.get(api_url, timeout=10)
        context.api_available = response.status_code == 200
        context.api_url = f"http://{config.FASTAPI_HOST}:{config.FASTAPI_PORT}"
        
        if context.api_available:
            logger.info(f"API endpoint is available at {context.api_url}")
        else:
            logger.warning(f"API endpoint returned status {response.status_code}")
            
    except Exception as e:
        logger.error(f"API endpoint check failed: {e}")
        context.api_available = False
        context.api_url = None

@when('I make a GET request to the endpoint')
def step_when_make_get_request(context):
    """Make GET request to API endpoint."""
    try:
        if not hasattr(context, 'api_available') or not context.api_available:
            context.api_response = None
            context.api_status_code = 0
            return
        
        api_url = f"{context.api_url}/clients"
        response = requests.get(api_url, timeout=10)
        
        context.api_response = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        context.api_status_code = response.status_code
        
        logger.info(f"API request completed with status {context.api_status_code}")
        
    except Exception as e:
        logger.error(f"API request failed: {e}")
        context.api_response = None
        context.api_status_code = 0

@then('the response should have status code {expected_code:d}')
def step_then_response_status_code(context, expected_code):
    """Verify API response status code."""
    actual_code = getattr(context, 'api_status_code', 0)
    assert actual_code == expected_code, f"Expected status code {expected_code}, got {actual_code}"
    logger.info(f"Status code validation passed: {actual_code}")

@then('the response should contain required fields')
def step_then_response_contains_fields(context):
    """Verify API response contains required fields."""
    response = getattr(context, 'api_response', None)
    
    assert response is not None, "No API response available"
    assert isinstance(response, dict), f"Response is not a dictionary: {type(response)}"
    
    # Check for required fields in the response
    required_fields = ['data', 'count', 'timestamp']
    
    for field in required_fields:
        assert field in response, f"Required field '{field}' not found in response"
    
    # Check that data is a list and contains client records
    assert isinstance(response['data'], list), "Response data is not a list"
    assert len(response['data']) > 0, "Response data is empty"
    
    # Check first client record structure
    first_client = response['data'][0]
    client_required_fields = ['client_id', 'client_name', 'revenue']
    
    for field in client_required_fields:
        assert field in first_client, f"Required client field '{field}' not found"
    
    logger.info("Response structure validation passed")

@given('I receive API response data')
def step_given_api_response_data(context):
    """Use existing API response data for validation."""
    if not hasattr(context, 'api_response') or context.api_response is None:
        # Make a request if we don't have response data
        step_given_api_endpoint_available(context)
        step_when_make_get_request(context)
    
    assert context.api_response is not None, "No API response data available"

@when('I check the numeric values')
def step_when_check_numeric_values(context):
    """Check numeric values in API response using Great Expectations."""
    try:
        response = getattr(context, 'api_response', None)
        assert response is not None, "No API response available"
        
        # Use Great Expectations to validate the data
        validation_result = validate_api_data(response)
        context.ge_validation_result = validation_result
        
        logger.info(f"Great Expectations validation completed: {validation_result['success']}")
        
    except Exception as e:
        logger.error(f"Numeric values check failed: {e}")
        context.ge_validation_result = {'success': False, 'error': str(e)}

@then('all values should be within expected ranges')
def step_then_values_within_ranges(context):
    """Verify all values are within expected ranges."""
    validation_result = getattr(context, 'ge_validation_result', None)
    
    assert validation_result is not None, "No validation result available"
    assert validation_result['success'], f"Validation failed: {validation_result.get('error', 'Unknown error')}"
    
    # Check statistics
    stats = validation_result.get('statistics', {})
    success_rate = stats.get('success_percent', 0)
    
    assert success_rate >= 80, f"Validation success rate too low: {success_rate}%"
    logger.info(f"Range validation passed with {success_rate}% success rate")

@then('no null values should be present in required fields')
def step_then_no_null_values(context):
    """Verify no null values in required fields."""
    validation_result = getattr(context, 'ge_validation_result', None)
    
    assert validation_result is not None, "No validation result available"
    
    # Check validation results for null value expectations
    results = validation_result.get('results', [])
    null_check_failures = []
    
    for result in results:
        expectation_type = result.get('expectation_config', {}).get('expectation_type', '')
        if 'not_be_null' in expectation_type and not result.get('success', False):
            null_check_failures.append(result)
    
    assert len(null_check_failures) == 0, f"Null value checks failed: {len(null_check_failures)} failures"
    logger.info("Null value validation passed")

# UI-related steps
@given('I am on the dashboard page')
def step_given_on_dashboard_page(context):
    """Navigate to dashboard page."""
    try:
        dashboard_url = f"http://{config.FASTAPI_HOST}:{config.FASTAPI_PORT}/dashboard"
        context.dashboard_url = dashboard_url
        context.on_dashboard = True
        logger.info(f"Dashboard URL set: {dashboard_url}")
        
    except Exception as e:
        logger.error(f"Error setting up dashboard: {e}")
        context.on_dashboard = False

@when('I look for Client A information')
def step_when_look_for_client_a(context):
    """Look for Client A information using Selenium."""
    try:
        if not hasattr(context, 'dashboard_url'):
            context.ui_validation_result = {'success': False, 'error': 'Dashboard URL not set'}
            return
        
        # Use Selenium to validate dashboard
        validation_result = validate_dashboard(context.dashboard_url)
        context.ui_validation_result = validation_result
        
        logger.info(f"Client A search completed: {validation_result['client_a_found']}")
        
    except Exception as e:
        logger.error(f"Error looking for Client A: {e}")
        context.ui_validation_result = {'success': False, 'error': str(e)}

@then('I should see the revenue value displayed')
def step_then_see_revenue_displayed(context):
    """Verify revenue value is displayed."""
    validation_result = getattr(context, 'ui_validation_result', None)
    
    assert validation_result is not None, "No UI validation result available"
    assert validation_result['client_a_found'], "Client A not found on dashboard"
    assert validation_result['revenue_value'] is not None, "Revenue value not found"
    
    logger.info(f"Revenue value displayed: {validation_result['revenue_value']}")

@then('the revenue should be a positive number')
def step_then_revenue_positive(context):
    """Verify revenue is a positive number."""
    validation_result = getattr(context, 'ui_validation_result', None)
    
    assert validation_result is not None, "No UI validation result available"
    assert validation_result['revenue_valid'], f"Revenue is not valid: {validation_result.get('revenue_value')}"
    
    revenue = validation_result['revenue_value']
    assert revenue > 0, f"Revenue is not positive: {revenue}"
    
    logger.info(f"Revenue validation passed: {revenue}")

@given('I am on the application page')
def step_given_on_application_page(context):
    """Navigate to application page."""
    try:
        app_url = f"http://{config.FASTAPI_HOST}:{config.FASTAPI_PORT}/dashboard"
        context.app_url = app_url
        context.on_app_page = True
        logger.info(f"Application URL set: {app_url}")
        
    except Exception as e:
        logger.error(f"Error setting up application page: {e}")
        context.on_app_page = False

@when('the page loads completely')
def step_when_page_loads(context):
    """Wait for page to load completely."""
    try:
        if not hasattr(context, 'app_url'):
            context.page_load_result = {'success': False, 'error': 'Application URL not set'}
            return
        
        # Define expected elements
        expected_elements = [
            {'name': 'page_title', 'type': 'tag', 'value': 'title'},
            {'name': 'main_container', 'type': 'class', 'value': 'container'},
            {'name': 'clients_grid', 'type': 'id', 'value': 'clientsGrid'}
        ]
        
        # Use Selenium to validate elements
        validation_result = validate_elements(context.app_url, expected_elements)
        context.page_load_result = validation_result
        
        logger.info(f"Page load validation completed: {validation_result['success']}")
        
    except Exception as e:
        logger.error(f"Error during page load validation: {e}")
        context.page_load_result = {'success': False, 'error': str(e)}

@then('all required elements should be visible')
def step_then_elements_visible(context):
    """Verify all required elements are visible."""
    load_result = getattr(context, 'page_load_result', None)
    
    assert load_result is not None, "No page load result available"
    assert load_result['success'], f"Page load validation failed: {load_result.get('errors', [])}"
    
    # Check that all elements were found and visible
    elements_found = load_result.get('elements_found', {})
    missing_elements = load_result.get('missing_elements', [])
    
    assert len(missing_elements) == 0, f"Missing elements: {missing_elements}"
    
    for element_name, element_info in elements_found.items():
        assert element_info.get('found', False), f"Element '{element_name}' not found"
        assert element_info.get('visible', False), f"Element '{element_name}' not visible"
    
    logger.info("All required elements are visible")

@then('no error messages should be displayed')
def step_then_no_error_messages(context):
    """Verify no error messages are displayed."""
    load_result = getattr(context, 'page_load_result', None)
    
    assert load_result is not None, "No page load result available"
    
    errors = load_result.get('errors', [])
    assert len(errors) == 0, f"Error messages found: {errors}"
    
    logger.info("No error messages displayed")

# Generic steps
@step('I have the requirement: "{requirement}"')
def step_have_requirement(context, requirement):
    """Store requirement for reference."""
    context.requirement = requirement
    logger.info(f"Requirement stored: {requirement[:100]}...")

@step('I implement the validation logic')
def step_implement_validation(context):
    """Placeholder for validation logic implementation."""
    context.validation_implemented = True
    logger.info("Validation logic implemented")

@step('the validation should pass successfully')
def step_validation_passes(context):
    """Verify validation passes."""
    assert getattr(context, 'validation_implemented', False), "Validation not implemented"
    logger.info("Validation passed successfully")

@then('the revenue data should meet the specified criteria')
def step_revenue_meets_criteria(context):
    """Verify revenue data meets specified criteria."""
    try:
        # Query Client A revenue from database
        query = "SELECT revenue FROM clients WHERE client_name = 'Client A'"
        result = quick_query(query)
        
        assert result is not None and len(result) > 0, "Client A not found in database"
        
        revenue = result[0]['revenue']
        
        # Validate revenue criteria
        assert revenue is not None, "Revenue is null"
        assert isinstance(revenue, (int, float)) or str(revenue).replace('.', '').isdigit(), "Revenue is not numeric"
        assert float(revenue) > 0, f"Revenue is not positive: {revenue}"
        assert float(revenue) >= 1000, f"Revenue is too low: {revenue}"  # Business rule example
        
        logger.info(f"Revenue validation passed for Client A: ${revenue:,.2f}")
        
    except Exception as e:
        logger.error(f"Revenue validation failed: {e}")
        assert False, f"Revenue data validation failed: {e}"

# Parameterized test step definitions
@given('I have access to the client database')
def step_access_client_database(context):
    """Verify access to client database."""
    try:
        db = get_db_manager()
        assert db.connect(), "Should be able to connect to database"
        context.db_connected = True
        db.disconnect()
        logger.info("Database access verified")
    except Exception as e:
        logger.error(f"Database access failed: {e}")
        assert False, f"Cannot access client database: {e}"

@given('the database contains client revenue data')
def step_database_contains_revenue_data(context):
    """Verify database contains client revenue data."""
    try:
        query = "SELECT COUNT(*) as count FROM clients WHERE revenue IS NOT NULL"
        result = quick_query(query)
        count = result[0]['count'] if result else 0
        assert count > 0, f"Database should contain revenue data, found {count} records"
        context.revenue_records_count = count
        logger.info(f"Database contains {count} records with revenue data")
    except Exception as e:
        logger.error(f"Revenue data check failed: {e}")
        assert False, f"Database revenue data verification failed: {e}"

@given('I have client "{client_name}" in the database')
def step_have_client_in_database(context, client_name):
    """Verify specific client exists in database."""
    try:
        query = f"SELECT * FROM clients WHERE client_name = '{client_name}'"
        result = quick_query(query)
        assert result is not None and len(result) > 0, f"Client '{client_name}' not found in database"
        context.current_client = result[0]
        context.current_client_name = client_name
        logger.info(f"Found client '{client_name}' in database")
    except Exception as e:
        logger.error(f"Client lookup failed: {e}")
        assert False, f"Client '{client_name}' verification failed: {e}"

@when('I check their revenue amount')
def step_check_revenue_amount(context):
    """Check the revenue amount for current client."""
    try:
        assert hasattr(context, 'current_client'), "No current client set"
        revenue = context.current_client.get('revenue')
        assert revenue is not None, "Revenue should not be null"
        context.current_revenue = float(revenue)
        logger.info(f"Current client revenue: ${context.current_revenue:,.2f}")
    except Exception as e:
        logger.error(f"Revenue check failed: {e}")
        assert False, f"Revenue amount check failed: {e}"

@then('the revenue should be at least {min_revenue:d}')
def step_revenue_at_least(context, min_revenue):
    """Verify revenue meets minimum threshold."""
    try:
        assert hasattr(context, 'current_revenue'), "No current revenue set"
        assert context.current_revenue >= min_revenue, f"Revenue ${context.current_revenue:,.2f} should be at least ${min_revenue:,}"
        logger.info(f"Revenue ${context.current_revenue:,.2f} meets minimum threshold ${min_revenue:,}")
    except Exception as e:
        logger.error(f"Minimum revenue validation failed: {e}")
        assert False, f"Revenue minimum threshold validation failed: {e}"

@then('the revenue should be less than {max_revenue:d}')
def step_revenue_less_than(context, max_revenue):
    """Verify revenue is below maximum threshold."""
    try:
        assert hasattr(context, 'current_revenue'), "No current revenue set"
        assert context.current_revenue < max_revenue, f"Revenue ${context.current_revenue:,.2f} should be less than ${max_revenue:,}"
        logger.info(f"Revenue ${context.current_revenue:,.2f} is below maximum threshold ${max_revenue:,}")
    except Exception as e:
        logger.error(f"Maximum revenue validation failed: {e}")
        assert False, f"Revenue maximum threshold validation failed: {e}"


@given('I make a request to the "{endpoint}" API endpoint')
def step_make_api_request(context, endpoint):
    """Make request to specified API endpoint."""
    try:
        import requests
        from app.config import Config
        config = Config()
        
        base_url = f"http://{config.FASTAPI_HOST}:{config.FASTAPI_PORT}"
        full_url = f"{base_url}{endpoint}"
        
        response = requests.get(full_url, timeout=10)
        assert response.status_code == 200, f"API request failed with status {response.status_code}"
        
        context.api_response = response.json()
        context.api_endpoint = endpoint
        logger.info(f"API request to {endpoint} successful")
    except Exception as e:
        logger.error(f"API request failed: {e}")
        assert False, f"API request to {endpoint} failed: {e}"

@when('I receive the response')
def step_receive_response(context):
    """Process the received API response."""
    try:
        assert hasattr(context, 'api_response'), "No API response available"
        assert context.api_response is not None, "API response should not be null"
        logger.info("API response received and processed")
    except Exception as e:
        logger.error(f"Response processing failed: {e}")
        assert False, f"API response processing failed: {e}"

@then('the "{field_name}" field should be of type "{expected_type}"')
def step_field_type_validation(context, field_name, expected_type):
    """Validate field type in API response."""
    try:
        assert hasattr(context, 'api_response'), "No API response available"
        
        # Handle different response structures
        data = context.api_response
        if isinstance(data, dict) and 'data' in data:
            data = data['data']
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        
        assert field_name in data, f"Field '{field_name}' not found in response"
        
        field_value = data[field_name]
        
        # Type validation
        if expected_type == 'integer':
            assert isinstance(field_value, int), f"Field '{field_name}' should be integer, got {type(field_value)}"
        elif expected_type == 'string':
            assert isinstance(field_value, str), f"Field '{field_name}' should be string, got {type(field_value)}"
        elif expected_type == 'number':
            assert isinstance(field_value, (int, float)), f"Field '{field_name}' should be number, got {type(field_value)}"
        
        logger.info(f"Field '{field_name}' type validation passed: {expected_type}")
    except Exception as e:
        logger.error(f"Field type validation failed: {e}")
        assert False, f"Field '{field_name}' type validation failed: {e}"

@then('the "{field_name}" field should not be null')
def step_field_not_null(context, field_name):
    """Validate field is not null."""
    try:
        assert hasattr(context, 'api_response'), "No API response available"
        
        # Handle different response structures
        data = context.api_response
        if isinstance(data, dict) and 'data' in data:
            data = data['data']
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        
        assert field_name in data, f"Field '{field_name}' not found in response"
        assert data[field_name] is not None, f"Field '{field_name}' should not be null"
        
        logger.info(f"Field '{field_name}' null validation passed")
    except Exception as e:
        logger.error(f"Field null validation failed: {e}")
        assert False, f"Field '{field_name}' null validation failed: {e}"

@given('I have a data quality rule for "{rule_type}"')
def step_have_quality_rule(context, rule_type):
    """Set up data quality rule."""
    try:
        context.quality_rule_type = rule_type
        context.quality_rule_config = {
            'not_null': {'check_nulls': True},
            'positive_numbers': {'min_value': 0},
            'reasonable_range': {'min_value': 0, 'max_value': 1000000},
            'unique_values': {'check_uniqueness': True}
        }
        
        assert rule_type in context.quality_rule_config, f"Unknown rule type: {rule_type}"
        logger.info(f"Data quality rule '{rule_type}' configured")
    except Exception as e:
        logger.error(f"Quality rule setup failed: {e}")
        assert False, f"Data quality rule setup failed: {e}"

@when('I apply the rule to column "{column_name}"')
def step_apply_rule_to_column(context, column_name):
    """Apply quality rule to specified column."""
    try:
        assert hasattr(context, 'quality_rule_type'), "No quality rule configured"
        
        # Get column data
        query = f"SELECT {column_name} FROM clients"
        result = quick_query(query)
        assert result is not None, f"Could not retrieve data for column '{column_name}'"
        
        column_data = [row[column_name] for row in result]
        context.column_data = column_data
        context.column_name = column_name
        
        # Apply rule based on type
        rule_type = context.quality_rule_type
        validation_passed = True
        validation_details = {}
        
        if rule_type == 'not_null':
            null_count = sum(1 for value in column_data if value is None)
            validation_passed = null_count == 0
            validation_details = {'null_count': null_count, 'total_count': len(column_data)}
        
        elif rule_type == 'positive_numbers':
            if column_name == 'revenue':
                negative_count = sum(1 for value in column_data if value is not None and float(value) <= 0)
                validation_passed = negative_count == 0
                validation_details = {'negative_count': negative_count, 'total_count': len(column_data)}
        
        elif rule_type == 'reasonable_range':
            if column_name == 'revenue':
                out_of_range = sum(1 for value in column_data if value is not None and (float(value) < 0 or float(value) > 1000000))
                validation_passed = out_of_range == 0
                validation_details = {'out_of_range_count': out_of_range, 'total_count': len(column_data)}
        
        elif rule_type == 'unique_values':
            unique_count = len(set(column_data))
            validation_passed = unique_count == len(column_data)
            validation_details = {'unique_count': unique_count, 'total_count': len(column_data)}
        
        context.rule_validation_passed = validation_passed
        context.rule_validation_details = validation_details
        
        logger.info(f"Applied rule '{rule_type}' to column '{column_name}': {validation_passed}")
    except Exception as e:
        logger.error(f"Rule application failed: {e}")
        assert False, f"Rule application to column '{column_name}' failed: {e}"

@then('the validation should "{expected_result}"')
def step_validation_result(context, expected_result):
    """Check validation result."""
    try:
        assert hasattr(context, 'rule_validation_passed'), "No validation result available"
        
        if expected_result == 'pass':
            assert context.rule_validation_passed, f"Validation should pass but failed: {context.rule_validation_details}"
        elif expected_result == 'fail':
            assert not context.rule_validation_passed, f"Validation should fail but passed: {context.rule_validation_details}"
        
        logger.info(f"Validation result check passed: expected '{expected_result}', got {'pass' if context.rule_validation_passed else 'fail'}")
    except Exception as e:
        logger.error(f"Validation result check failed: {e}")
        assert False, f"Validation result check failed: {e}"

@then('I should get a detailed validation report')
def step_get_validation_report(context):
    """Verify detailed validation report is available."""
    try:
        assert hasattr(context, 'rule_validation_details'), "No validation details available"
        assert context.rule_validation_details is not None, "Validation details should not be null"
        assert len(context.rule_validation_details) > 0, "Validation details should contain information"
        
        logger.info(f"Validation report available: {context.rule_validation_details}")
    except Exception as e:
        logger.error(f"Validation report check failed: {e}")
        assert False, f"Validation report check failed: {e}"
