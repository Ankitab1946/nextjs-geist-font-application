Feature: UI Validation
  As a user
  I want to verify UI elements display correctly
  So that I can trust the application interface

  @ui
  Scenario: Validate revenue display
    Given I am on the dashboard page
    When I look for Client A information
    Then I should see the revenue value displayed
    And the revenue should be a positive number

  @ui
  Scenario: Validate page elements
    Given I am on the application page
    When the page loads completely
    Then all required elements should be visible
    And no error messages should be displayed
