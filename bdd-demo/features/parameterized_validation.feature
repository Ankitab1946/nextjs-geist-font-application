Feature: Parameterized Data Validation
  As a data analyst
  I want to validate multiple clients' data using parameters
  So that I can efficiently test various scenarios

  Background:
    Given I have access to the client database
    And the database contains client revenue data

  @parametrize @database
  Scenario Outline: Validate client revenue thresholds
    Given I have client "<client_name>" in the database
    When I check their revenue amount
    Then the revenue should be at least <min_revenue>
    And the revenue should be less than <max_revenue>
    And the revenue should be a positive number

    Examples:
      | client_name | min_revenue | max_revenue |
      | Client A    | 100000      | 200000      |
      | Client B    | 200000      | 300000      |
      | Client C    | 50000       | 150000      |

  @parametrize @api
  Scenario Outline: Validate API response data types
    Given I make a request to the "<endpoint>" API endpoint
    When I receive the response
    Then the "<field_name>" field should be of type "<expected_type>"
    And the "<field_name>" field should not be null

    Examples:
      | endpoint | field_name  | expected_type |
      | /clients | client_id   | integer       |
      | /clients | client_name | string        |
      | /clients | revenue     | number        |
      | /clients | created_at  | string        |

  @parametrize @database
  Scenario Outline: Validate data quality rules
    Given I have a data quality rule for "<rule_type>"
    When I apply the rule to column "<column_name>"
    Then the validation should "<expected_result>"
    And I should get a detailed validation report

    Examples:
      | rule_type           | column_name | expected_result |
      | not_null           | client_name | pass            |
      | not_null           | revenue     | pass            |
      | positive_numbers   | revenue     | pass            |
      | reasonable_range   | revenue     | pass            |
      | unique_values      | client_id   | pass            |

  @parametrize @integration
  Scenario Outline: Cross-system data consistency
    Given I have data in the "<source_system>"
    And I have corresponding data in the "<target_system>"
    When I compare the "<field_name>" values
    Then the values should match exactly
    And there should be no data discrepancies

    Examples:
      | source_system | target_system | field_name  |
      | CSV_Feed      | Database      | client_name |
      | CSV_Feed      | Database      | revenue     |
      | Database      | API_Response  | client_id   |
      | Database      | API_Response  | client_name |

  Scenario: Generate comprehensive validation report
    Given I have executed all parameterized validation scenarios
    When I generate a comprehensive report
    Then the report should include all test results
    And the report should show pass/fail statistics
    And the report should include detailed error information for failures
    And the report should be available in multiple formats (HTML, JSON, PDF)
