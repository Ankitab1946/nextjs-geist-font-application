Feature: Data Validation
  As a data analyst
  I want to validate data quality
  So that I can ensure data integrity

  @database
  Scenario: Validate data count
    Given I have a source data file "sample_feed.csv"
    When I load the data into the database
    Then the record count should match the source file
    And all required fields should be populated

  @database
  Scenario: Validate data types
    Given I have data in the database
    When I check the data types
    Then all numeric fields should contain valid numbers
    And all date fields should contain valid dates
