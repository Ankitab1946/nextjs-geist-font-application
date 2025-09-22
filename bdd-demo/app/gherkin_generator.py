"""Gherkin generator module that mocks AWS Bedrock for converting English to Gherkin."""

import json
import time
import random
from typing import Optional, Dict, Any
from app.config import Config
from app.utils import setup_logging, save_text_file, sanitize_filename

logger = setup_logging()

class GherkinGenerator:
    """Mock AWS Bedrock service for generating Gherkin from English requirements."""
    
    def __init__(self):
        self.config = Config()
        self.mock_templates = {
            'data_validation': """Feature: Data Validation
  As a data analyst
  I want to validate data quality
  So that I can ensure data integrity

  Scenario: Validate data count
    Given I have a source data file
    When I load the data into the database
    Then the record count should match the source file
    And all required fields should be populated

  Scenario: Validate data types
    Given I have data in the database
    When I check the data types
    Then all numeric fields should contain valid numbers
    And all date fields should contain valid dates""",
            
            'api_testing': """Feature: API Data Quality
  As a QA engineer
  I want to test API data quality
  So that I can ensure API responses are valid

  Scenario: Validate API response structure
    Given the API endpoint is available
    When I make a GET request to the endpoint
    Then the response should have status code 200
    And the response should contain required fields

  Scenario: Validate API data ranges
    Given I receive API response data
    When I check the numeric values
    Then all values should be within expected ranges
    And no null values should be present in required fields""",
            
            'ui_testing': """Feature: UI Validation
  As a user
  I want to verify UI elements display correctly
  So that I can trust the application interface

  Scenario: Validate revenue display
    Given I am on the dashboard page
    When I look for Client A information
    Then I should see the revenue value displayed
    And the revenue should be a positive number

  Scenario: Validate page elements
    Given I am on the application page
    When the page loads completely
    Then all required elements should be visible
    And no error messages should be displayed"""
        }
    
    def generate_gherkin(self, english_requirement: str) -> Dict[str, Any]:
        """
        Generate Gherkin feature file from English requirement.
        Mocks AWS Bedrock API call.
        """
        try:
            logger.info(f"Generating Gherkin for requirement: {english_requirement[:100]}...")
            
            if self.config.MOCK_MODE:
                return self._mock_bedrock_call(english_requirement)
            else:
                return self._real_bedrock_call(english_requirement)
                
        except Exception as e:
            logger.error(f"Error generating Gherkin: {e}")
            return {
                'success': False,
                'error': str(e),
                'gherkin_content': None,
                'feature_filename': None
            }
    
    def _mock_bedrock_call(self, requirement: str) -> Dict[str, Any]:
        """Mock AWS Bedrock API call with simulated processing time."""
        # Simulate API processing time
        time.sleep(random.uniform(1, 3))
        
        # Determine which template to use based on keywords
        requirement_lower = requirement.lower()
        
        if any(keyword in requirement_lower for keyword in ['data', 'database', 'csv', 'feed', 'count']):
            template_key = 'data_validation'
            feature_name = 'data_validation'
        elif any(keyword in requirement_lower for keyword in ['api', 'endpoint', 'response', 'json']):
            template_key = 'api_testing'
            feature_name = 'api_testing'
        elif any(keyword in requirement_lower for keyword in ['ui', 'interface', 'page', 'revenue', 'client']):
            template_key = 'ui_testing'
            feature_name = 'ui_validation'
        else:
            # Default to data validation
            template_key = 'data_validation'
            feature_name = 'generic_validation'
        
        # Get template and customize it
        gherkin_content = self.mock_templates[template_key]
        
        # Add custom scenario based on requirement
        custom_scenario = self._generate_custom_scenario(requirement)
        if custom_scenario:
            gherkin_content += f"\n\n{custom_scenario}"
        
        # Generate filename
        feature_filename = f"{sanitize_filename(feature_name)}.feature"
        
        # Save to features directory
        feature_path = f"{self.config.FEATURES_DIR}/{feature_filename}"
        success = save_text_file(gherkin_content, feature_path)
        
        return {
            'success': success,
            'gherkin_content': gherkin_content,
            'feature_filename': feature_filename,
            'feature_path': feature_path,
            'model_used': self.config.BEDROCK_MODEL_ID,
            'processing_time': random.uniform(1.5, 2.8)
        }
    
    def _generate_custom_scenario(self, requirement: str) -> Optional[str]:
        """Generate a custom scenario based on the requirement text."""
        requirement_words = requirement.lower().split()
        
        # Simple keyword-based scenario generation
        if 'revenue' in requirement_words:
            return """  Scenario: Custom revenue validation
    Given I have the requirement: "{}"
    When I implement the validation logic
    Then the revenue data should meet the specified criteria
    And the validation should pass successfully""".format(requirement[:100])
        
        elif 'count' in requirement_words or 'records' in requirement_words:
            return """  Scenario: Custom record count validation
    Given I have the requirement: "{}"
    When I count the records
    Then the count should match expectations
    And no data should be missing""".format(requirement[:100])
        
        return None
    
    def _real_bedrock_call(self, requirement: str) -> Dict[str, Any]:
        """
        Real AWS Bedrock API call (placeholder for actual implementation).
        This would be implemented when real AWS credentials are available.
        """
        # This is a placeholder for real AWS Bedrock integration
        # In a real implementation, you would:
        # 1. Initialize boto3 client for Bedrock
        # 2. Prepare the prompt for Claude
        # 3. Make the API call
        # 4. Parse the response
        
        logger.warning("Real Bedrock API not implemented. Using mock instead.")
        return self._mock_bedrock_call(requirement)
    
    def list_generated_features(self) -> list:
        """List all generated feature files."""
        import os
        features_dir = self.config.FEATURES_DIR
        
        if not os.path.exists(features_dir):
            return []
        
        feature_files = []
        for filename in os.listdir(features_dir):
            if filename.endswith('.feature'):
                filepath = os.path.join(features_dir, filename)
                feature_files.append({
                    'filename': filename,
                    'filepath': filepath,
                    'size_kb': round(os.path.getsize(filepath) / 1024, 2),
                    'modified': os.path.getmtime(filepath)
                })
        
        return sorted(feature_files, key=lambda x: x['modified'], reverse=True)
    
    def validate_gherkin_syntax(self, gherkin_content: str) -> Dict[str, Any]:
        """Basic validation of Gherkin syntax."""
        lines = gherkin_content.split('\n')
        errors = []
        warnings = []
        
        has_feature = False
        has_scenario = False
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            if line.startswith('Feature:'):
                has_feature = True
            elif line.startswith('Scenario:'):
                has_scenario = True
            elif line.startswith('Given ') or line.startswith('When ') or line.startswith('Then ') or line.startswith('And '):
                if not has_scenario:
                    errors.append(f"Line {i}: Step found outside of scenario")
        
        if not has_feature:
            errors.append("No Feature declaration found")
        if not has_scenario:
            warnings.append("No Scenario found")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
