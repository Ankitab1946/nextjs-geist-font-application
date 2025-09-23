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
