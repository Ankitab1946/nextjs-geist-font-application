# Detailed Implementation Plan for BDD + Gherkin Demo Project with Jira Xray Integration

This plan outlines the step-by-step changes and files to be created for a production-ready Python demo project that converts English requirements to Gherkin using AWS Bedrock (mocked), runs BDD tests with Behave, and integrates test results with Jira Xray (mocked). The UI is built with Streamlit.

---

## Project Structure Overview

```
bdd-demo/

├── features/
│   ├── *.feature                # Generated Gherkin feature files
│   ├── steps/
│   │   ├── step_definitions.py # Behave step definitions
│   │   └── environment.py       # Behave environment hooks
├── app/
│   ├── streamlit_app.py         # Streamlit UI app entrypoint
│   ├── fastapi_mock_api.py      # FastAPI mock API for scenario 2
│   ├── selenium_tests.py        # Selenium UI validation tests
│   ├── behave_runner.py         # Module to run Behave programmatically
│   ├── gherkin_generator.py     # Module to convert English to Gherkin (mock AWS Bedrock)
│   ├── xray_integration.py      # Module to upload reports to Jira Xray (mocked)
│   ├── config.py                # Configuration flags and settings
│   ├── db_utils.py              # SQLite and optional SQL Server DB helpers
│   ├── ge_checks.py             # Great Expectations data quality checks
│   └── utils.py                 # Utility functions (logging, file handling)
├── data/
│   ├── sample_feed.csv          # Sample CSV feed for scenario 1
│   └── ge_data_docs/            # Generated Great Expectations Data Docs
├── screenshots/                 # Selenium screenshots saved here
├── reports/
│   ├── cucumber_report.json    # Generated Cucumber JSON report
│   └── test_execution_summary.html # Downloadable test execution summary
├── .env.sample                  # Sample environment variables file
├── requirements.txt             # Python dependencies
├── README.md                   # Documentation and setup instructions
└── pytest.ini                  # Pytest configuration for DB checks
```

---

## Step-by-Step File and Feature Implementation

### 1. `app/streamlit_app.py` - Streamlit UI

- **Features:**
  - Text input box for user to enter plain English requirement.
  - Button to generate Gherkin `.feature` file using mocked AWS Bedrock.
  - Display generated Gherkin in a syntax-highlighted code block.
  - Save `.feature` files under `features/` directory.
  - Button to run Behave tests live, showing pass/fail status per scenario.
  - Display clickable links to screenshots folder.
  - Button to export `cucumber_report.json` and upload to Jira Xray (mocked).
  - Show Test Execution key and deep links to Jira issues.
  - Button to download test execution summary as HTML.
  - Config toggle to switch between SQLite and SQL Server mode.
- **UI/UX:**
  - Clean, modern layout with clear typography and spacing.
  - Use color-coded badges for pass/fail statuses.
  - Responsive layout with sidebar for logs and links.
  - No icons or external images; use typography and color only.

### 2. `app/gherkin_generator.py` - English to Gherkin Conversion

- **Features:**
  - Mock implementation simulating AWS Bedrock Anthropic Claude model.
  - Accept English text input, return well-formed Gherkin feature text.
  - Include error handling for empty input or API failures (mocked).
  - Save generated Gherkin to `.feature` files in `features/`.

### 3. `features/` Directory

- **Features:**
  - Store generated `.feature` files.
  - Include three concrete scenarios as `.feature` files:
    1. Feed to DB validation (count parity, data types).
    2. API data quality with Great Expectations.
    3. UI validation of Revenue using Selenium.
- **Steps:**
  - Create `steps/step_definitions.py` with Behave step implementations.
  - Use `pytest` for DB assertions.
  - Use `Great Expectations` for data quality checks.
  - Use `Selenium` with ChromeDriver for UI validation.
  - Save screenshots on test pass/fail in `screenshots/`.

### 4. `app/behave_runner.py` - Behave Execution Module

- **Features:**
  - Programmatically run Behave tests from Streamlit UI.
  - Capture and parse test results (pass/fail).
  - Generate `cucumber_report.json` in `reports/`.
  - Provide hooks to link screenshots and GE Data Docs.
  - Handle errors gracefully and report to UI.

### 5. `app/xray_integration.py` - Jira Xray Upload (Mocked)

- **Features:**
  - Mock REST API client to simulate uploading `cucumber_report.json`.
  - Return fake Test Execution key and Jira issue links.
  - Provide functions to generate deep links to Jira UI.
  - Handle API errors and show messages in UI.

### 6. `app/fastapi_mock_api.py` - Mock API for Scenario 2

- **Features:**
  - FastAPI app serving JSON with numeric attributes.
  - Endpoint returns sample data for Great Expectations validation.
  - Run locally alongside Streamlit app.

### 7. `app/selenium_tests.py` - Selenium UI Validation

- **Features:**
  - Selenium test to open demo web page (FastAPI or Streamlit).
  - Find Client A and assert Revenue value.
  - Save screenshots on pass/fail in `screenshots/`.
  - Integrate with Behave steps.

### 8. `app/db_utils.py` - Database Helpers

- **Features:**
  - SQLite connection and query helpers.
  - Optional SQL Server connection using `pyodbc` with Windows Auth.
  - Config flag to switch DB mode.
  - Sample data loading from CSV feed.

### 9. `app/ge_checks.py` - Great Expectations Checks

- **Features:**
  - Define GE suite and checkpoint in code.
  - Validate API JSON attribute ranges.
  - Persist GE Data Docs locally under `data/ge_data_docs/`.
  - Integrate with Behave steps.

### 10. `app/config.py` - Configuration

- **Features:**
  - Central config for toggles (DB mode, mock mode).
  - Load environment variables from `.env` file.
  - Provide default values and validation.

### 11. `app/utils.py` - Utility Functions

- **Features:**
  - Logging setup.
  - File read/write helpers.
  - Timestamp and metadata utilities.
  - Commit hash retrieval (if available).

### 12. `requirements.txt`

- Include all dependencies:
  - streamlit
  - behave
  - pytest
  - great_expectations
  - selenium
  - fastapi
  - uvicorn
  - pyodbc (optional)
  - boto3 (for AWS Bedrock mock)
  - requests (for Jira API mock)
  - python-dotenv

### 13. `.env.sample`

- Provide sample environment variables for AWS and Jira keys (placeholders).
- Document usage and how to create `.env` file.

### 14. `README.md`

- Detailed setup instructions.
- How to run Streamlit UI.
- How to switch DB modes.
- How to run tests manually.
- Explanation of mock modes.
- How to extend with real AWS/Jira credentials.

---

## Error Handling and Best Practices

- Validate all user inputs in Streamlit UI.
- Catch and display errors from mocked AWS Bedrock and Jira API calls.
- Use try-except blocks in Behave steps to avoid test crashes.
- Log all key events and errors to console and optionally to file.
- Ensure all file writes are atomic and handle permission errors.
- Use environment variables securely; do not commit secrets.
- Provide clear user feedback in UI for all operations.
- Use consistent code style and type hints for maintainability.

---

## UI/UX Considerations

- Minimalist, clean UI with clear sections:
  - Input area for English requirements.
  - Generated Gherkin display with copy/save options.
  - Test execution panel with real-time status.
  - Links panel for screenshots, reports, Jira issues.
- Use Tailwind-like spacing and typography principles in Streamlit (via markdown and st components).
- Responsive layout for desktop and tablet.
- Use color-coded badges (green/red) for pass/fail.
- Provide loading spinners during long operations.
- Allow user to download reports and summaries easily.

---

# Summary

- Created a new Python project with Streamlit UI for English to Gherkin conversion using mocked AWS Bedrock.
- Implemented Behave BDD tests for three concrete scenarios with pytest, Great Expectations, and Selenium.
- Added FastAPI mock API and SQLite/SQL Server DB support with config toggle.
- Developed mocked Jira Xray integration to upload Cucumber JSON and show test execution links.
- Designed a modern, clean Streamlit UI with real-time test execution, screenshots, and report downloads.
- Included robust error handling, logging, and environment variable management.
- Provided sample `.env` and detailed README for easy setup and extension.
- Ensured all generated files and reports are saved in organized folders for easy access.
- The demo runs fully locally with mock integrations, enabling easy testing without real AWS or Jira credentials.
