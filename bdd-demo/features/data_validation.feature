Feature: Data Validation
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
    And all date fields should contain valid dates

  Scenario: Custom revenue validation
    Given I have the requirement: "I want to validate that the revenue data for Client A is displayed correctly on the dashboard and sh"
    When I implement the validation logic
    Then the revenue data should meet the specified criteria
    And the validation should pass successfully