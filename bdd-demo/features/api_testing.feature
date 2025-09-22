Feature: API Data Quality
  As a QA engineer
  I want to test API data quality
  So that I can ensure API responses are valid

  @api
  Scenario: Validate API response structure
    Given the API endpoint is available
    When I make a GET request to the endpoint
    Then the response should have status code 200
    And the response should contain required fields

  @api
  Scenario: Validate API data ranges
    Given I receive API response data
    When I check the numeric values
    Then all values should be within expected ranges
    And no null values should be present in required fields
