"""Behave environment hooks for BDD test setup and teardown."""

import os
import logging
import subprocess
import time
from app.config import Config
from app.db_utils import get_db_manager
from app.utils import setup_logging, ensure_directory_exists

# Setup logging
logger = setup_logging()
config = Config()

def before_all(context):
    """Setup before all tests."""
    logger.info("=== BDD Test Suite Starting ===")
    
    # Setup test environment
    context.config = config
    context.test_data_setup = False
    context.api_server_started = False
    context.api_server_process = None
    
    # Ensure required directories exist
    ensure_directory_exists('data')
    ensure_directory_exists('screenshots')
    ensure_directory_exists('reports')
    ensure_directory_exists('features')
    
    # Setup database and sample data
    setup_test_database(context)
    
    # Start FastAPI server for testing
    start_api_server(context)
    
    logger.info("Test environment setup completed")

def before_feature(context, feature):
    """Setup before each feature."""
    logger.info(f"Starting feature: {feature.name}")
    context.feature_name = feature.name
    context.feature_start_time = time.time()

def before_scenario(context, scenario):
    """Setup before each scenario."""
    logger.info(f"Starting scenario: {scenario.name}")
    context.scenario_name = scenario.name
    context.scenario_start_time = time.time()
    
    # Reset scenario-specific context
    context.scenario_errors = []
    context.scenario_screenshots = []

def after_scenario(context, scenario):
    """Cleanup after each scenario."""
    duration = time.time() - getattr(context, 'scenario_start_time', time.time())
    status = "PASSED" if scenario.status == "passed" else "FAILED"
    
    logger.info(f"Scenario '{scenario.name}' {status} in {duration:.2f}s")
    
    # Log any errors that occurred
    if hasattr(context, 'scenario_errors') and context.scenario_errors:
        for error in context.scenario_errors:
            logger.error(f"Scenario error: {error}")
    
    # Log screenshots taken
    if hasattr(context, 'scenario_screenshots') and context.scenario_screenshots:
        for screenshot in context.scenario_screenshots:
            logger.info(f"Screenshot saved: {screenshot}")

def after_feature(context, feature):
    """Cleanup after each feature."""
    duration = time.time() - getattr(context, 'feature_start_time', time.time())
    
    # Count scenario results
    passed_scenarios = sum(1 for scenario in feature.scenarios if scenario.status == "passed")
    total_scenarios = len(feature.scenarios)
    
    logger.info(f"Feature '{feature.name}' completed in {duration:.2f}s")
    logger.info(f"Scenarios: {passed_scenarios}/{total_scenarios} passed")

def after_all(context):
    """Cleanup after all tests."""
    logger.info("=== BDD Test Suite Completed ===")
    
    # Stop API server
    stop_api_server(context)
    
    # Cleanup database connections
    cleanup_database(context)
    
    logger.info("Test environment cleanup completed")

def setup_test_database(context):
    """Setup test database with sample data."""
    try:
        logger.info("Setting up test database...")
        
        db = get_db_manager()
        
        # Setup sample data
        success = db.setup_sample_data()
        
        if success:
            context.test_data_setup = True
            logger.info("Test database setup completed successfully")
        else:
            logger.error("Test database setup failed")
            context.test_data_setup = False
        
        db.disconnect()
        
    except Exception as e:
        logger.error(f"Error setting up test database: {e}")
        context.test_data_setup = False

def start_api_server(context):
    """Start FastAPI server for testing."""
    try:
        logger.info("Starting FastAPI test server...")
        
        # Check if server is already running
        import requests
        try:
            response = requests.get(f"http://{config.FASTAPI_HOST}:{config.FASTAPI_PORT}/health", timeout=2)
            if response.status_code == 200:
                logger.info("FastAPI server already running")
                context.api_server_started = True
                return
        except requests.exceptions.RequestException:
            pass  # Server not running, we'll start it
        
        # Start the server
        server_cmd = [
            "python", "-m", "uvicorn", 
            "app.fastapi_mock_api:app",
            "--host", config.FASTAPI_HOST,
            "--port", str(config.FASTAPI_PORT),
            "--log-level", "warning"  # Reduce log noise during tests
        ]
        
        context.api_server_process = subprocess.Popen(
            server_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.getcwd()
        )
        
        # Wait for server to start
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                time.sleep(1)
                response = requests.get(f"http://{config.FASTAPI_HOST}:{config.FASTAPI_PORT}/health", timeout=2)
                if response.status_code == 200:
                    context.api_server_started = True
                    logger.info(f"FastAPI server started successfully on {config.FASTAPI_HOST}:{config.FASTAPI_PORT}")
                    return
            except requests.exceptions.RequestException:
                continue
        
        logger.error("Failed to start FastAPI server within timeout")
        context.api_server_started = False
        
    except Exception as e:
        logger.error(f"Error starting FastAPI server: {e}")
        context.api_server_started = False

def stop_api_server(context):
    """Stop FastAPI server."""
    try:
        if hasattr(context, 'api_server_process') and context.api_server_process:
            logger.info("Stopping FastAPI test server...")
            context.api_server_process.terminate()
            
            # Wait for process to terminate
            try:
                context.api_server_process.wait(timeout=5)
                logger.info("FastAPI server stopped successfully")
            except subprocess.TimeoutExpired:
                logger.warning("FastAPI server didn't stop gracefully, killing...")
                context.api_server_process.kill()
                context.api_server_process.wait()
            
            context.api_server_process = None
            
    except Exception as e:
        logger.error(f"Error stopping FastAPI server: {e}")

def cleanup_database(context):
    """Cleanup database connections."""
    try:
        # This is mainly for cleanup of any remaining connections
        # SQLite doesn't require much cleanup, but SQL Server might
        logger.info("Cleaning up database connections...")
        
        # Any additional cleanup can be added here
        
    except Exception as e:
        logger.error(f"Error during database cleanup: {e}")

# Error handling hooks
def after_step(context, step):
    """Handle step completion."""
    if step.status == "failed":
        logger.error(f"Step failed: {step.name}")
        
        # Add error to scenario context
        if not hasattr(context, 'scenario_errors'):
            context.scenario_errors = []
        
        context.scenario_errors.append(f"Step '{step.name}' failed: {step.exception}")
        
        # Take screenshot if this is a UI-related step
        if any(keyword in step.name.lower() for keyword in ['dashboard', 'page', 'ui', 'browser', 'client']):
            try:
                from app.selenium_tests import SeleniumUITester
                tester = SeleniumUITester()
                if tester.setup_driver():
                    screenshot_path = tester.take_screenshot(
                        f"failed_step_{step.name.replace(' ', '_')}", 
                        f"Screenshot after failed step: {step.name}"
                    )
                    if screenshot_path:
                        if not hasattr(context, 'scenario_screenshots'):
                            context.scenario_screenshots = []
                        context.scenario_screenshots.append(screenshot_path)
                    tester.teardown_driver()
            except Exception as e:
                logger.error(f"Error taking screenshot after failed step: {e}")

# Custom context attributes
def setup_context_attributes(context):
    """Setup custom context attributes."""
    context.test_config = config
    context.screenshots_taken = []
    context.api_responses = {}
    context.db_queries_executed = []
    context.validation_results = {}

# Hook to setup context
def before_tag(context, tag):
    """Handle specific tags."""
    if tag == "database":
        logger.info("Database-related scenario detected")
        # Ensure database is ready
        if not getattr(context, 'test_data_setup', False):
            setup_test_database(context)
    
    elif tag == "api":
        logger.info("API-related scenario detected")
        # Ensure API server is running
        if not getattr(context, 'api_server_started', False):
            start_api_server(context)
    
    elif tag == "ui":
        logger.info("UI-related scenario detected")
        # Setup for UI testing
        ensure_directory_exists('screenshots')
        
        # Ensure API server is running for UI tests
        if not getattr(context, 'api_server_started', False):
            start_api_server(context)

# Initialize context on import
def initialize_context():
    """Initialize any global context needed."""
    # Setup logging format for behave
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Behave environment initialized")

# Call initialization
initialize_context()
