# BDD Demo - Gherkin Generator & Test Runner

A production-ready, end-to-end demo project that demonstrates how BDD + Gherkin converts plain English requirements into automated tests and integrates with Jira Xray.

## 🎯 Overview

This demo showcases:
- **English to Gherkin conversion** using mocked AWS Bedrock (Claude)
- **BDD test execution** with Behave framework
- **Data validation** with Great Expectations
- **UI testing** with Selenium WebDriver
- **API testing** with FastAPI mock server
- **Jira Xray integration** (mocked for demo purposes)

## 🏗️ Architecture

```
bdd-demo/
├── app/                          # Core application modules
│   ├── streamlit_app.py         # Main Streamlit UI
│   ├── config.py                # Configuration settings
│   ├── gherkin_generator.py     # English → Gherkin conversion
│   ├── behave_runner.py         # BDD test execution
│   ├── xray_integration.py      # Jira Xray integration
│   ├── db_utils.py              # Database utilities
│   ├── ge_checks.py             # Great Expectations checks
│   ├── fastapi_mock_api.py      # Mock API server
│   ├── selenium_tests.py        # UI test utilities
│   └── utils.py                 # Common utilities
├── features/                     # BDD feature files
│   ├── data_validation.feature  # DB validation scenarios
│   ├── api_testing.feature      # API testing scenarios
│   ├── ui_validation.feature    # UI testing scenarios
│   └── steps/                   # Step definitions
│       ├── step_definitions.py  # Behave step implementations
│       └── environment.py       # Test environment setup
├── data/                        # Sample data and databases
│   └── sample_feed.csv          # Sample CSV data
├── reports/                     # Generated test reports
├── screenshots/                 # Selenium screenshots
└── requirements.txt             # Python dependencies
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Chrome browser** (for Selenium tests)
- **Git** (optional, for version control)

### 1. Installation

```bash
# Navigate to the bdd-demo directory
cd bdd-demo

# Install Python dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p screenshots reports data/ge_data_docs
```

### 2. Environment Setup (Optional)

Create a `.env` file for custom configuration:

```bash
# Database settings
USE_SQL_SERVER=false
SQLITE_DB_PATH=data/demo.db

# Mock mode (recommended for demo)
MOCK_MODE=true
DEBUG=true

# FastAPI server settings
FASTAPI_HOST=127.0.0.1
FASTAPI_PORT=8001

# Selenium settings
SELENIUM_HEADLESS=true
SELENIUM_TIMEOUT=10

# AWS Bedrock (mocked)
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Jira Xray (mocked)
JIRA_BASE_URL=https://your-company.atlassian.net
XRAY_PROJECT_KEY=DEMO
```

### 3. Run the Demo

```bash
# Start the Streamlit application
streamlit run app/streamlit_app.py --server.port 8000
```

The application will open in your browser at: **http://localhost:8000**

## 🎮 Using the Demo

### Step 1: Generate Gherkin
1. Navigate to the **"Generate Gherkin"** tab
2. Enter a requirement in plain English, for example:
   ```
   I want to validate that the revenue data for Client A is displayed 
   correctly on the dashboard and shows a positive number.
   ```
3. Click **"Generate Gherkin"**
4. Review the generated `.feature` file

### Step 2: Run BDD Tests
1. Go to the **"Run Tests"** tab
2. The API server will start automatically
3. Select features to run or click **"Run All Tests"**
4. View real-time test results with pass/fail status
5. Check generated screenshots in the results

### Step 3: Xray Integration
1. Navigate to the **"Xray Integration"** tab
2. Upload Cucumber JSON reports to mocked Jira Xray
3. Create test plans and view execution links
4. Download test execution summaries

### Step 4: Download Reports
1. Go to the **"Downloads"** tab
2. Download test reports (JSON, XML, HTML)
3. Download screenshots from UI tests
4. Download Great Expectations data docs

## 🧪 Test Scenarios

The demo includes three pre-built scenarios:

### 1. Data Validation (Feed → Database)
- **File**: `features/data_validation.feature`
- **Purpose**: Validates data consistency between CSV feed and SQLite database
- **Tests**: Row count parity, data type verification
- **Tools**: pytest, pandas, SQLite

### 2. API Data Quality
- **File**: `features/api_testing.feature`
- **Purpose**: Validates API responses using Great Expectations
- **Tests**: JSON structure, numeric ranges, data quality rules
- **Tools**: Great Expectations, FastAPI mock server

### 3. UI Validation
- **File**: `features/ui_validation.feature`
- **Purpose**: Validates web UI elements and data display
- **Tests**: Client revenue display, UI element presence
- **Tools**: Selenium WebDriver, Chrome browser

## 🔧 Configuration Options

### Database Modes
- **SQLite** (default): Uses local SQLite database
- **SQL Server**: Set `USE_SQL_SERVER=true` in `.env`

### Mock vs Real APIs
- **Mock Mode** (default): Uses simulated AWS Bedrock and Jira Xray
- **Real APIs**: Set `MOCK_MODE=false` and provide real credentials

### Selenium Options
- **Headless** (default): Runs Chrome in headless mode
- **Headed**: Set `SELENIUM_HEADLESS=false` to see browser

## 📊 Generated Artifacts

### Test Reports
- **Cucumber JSON**: `reports/cucumber_report_TIMESTAMP.json`
- **JUnit XML**: `reports/junit_report_TIMESTAMP.xml`
- **HTML Reports**: Custom HTML summaries

### Screenshots
- **UI Tests**: `screenshots/ui_test_TIMESTAMP.png`
- **Error Screenshots**: Captured on test failures

### Data Documentation
- **Great Expectations**: `data/ge_data_docs/index.html`
- **Data Profiling**: Automated data quality reports

## 🔗 API Endpoints

When the FastAPI mock server is running (http://127.0.0.1:8001):

- **Health Check**: `GET /health`
- **Dashboard**: `GET /dashboard` (HTML page for UI tests)
- **Clients API**: `GET /clients` (JSON data for API tests)
- **Metrics**: `GET /metrics` (Numeric data for GE validation)

## 🐛 Troubleshooting

### Common Issues

1. **Chrome Driver Issues**
   ```bash
   # The demo uses webdriver-manager to auto-download ChromeDriver
   # If issues persist, install Chrome manually
   ```

2. **Port Conflicts**
   ```bash
   # Change ports in .env file
   FASTAPI_PORT=8002  # Change from default 8001
   ```

3. **Permission Errors**
   ```bash
   # Ensure write permissions for directories
   chmod -R 755 screenshots reports data
   ```

4. **Module Import Errors**
   ```bash
   # Ensure you're in the bdd-demo directory
   cd bdd-demo
   export PYTHONPATH=$PYTHONPATH:$(pwd)
   ```

### Debug Mode

Enable debug logging:
```bash
export DEBUG=true
streamlit run app/streamlit_app.py --server.port 8000 --logger.level debug
```

## 🔐 Production Setup

For production use with real APIs:

### 1. AWS Bedrock Setup
```bash
# Set real AWS credentials
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_SESSION_TOKEN=your_session_token
export AWS_REGION=us-east-1
export MOCK_MODE=false
```

### 2. Jira Xray Setup
```bash
# Set real Jira credentials
export JIRA_BASE_URL=https://your-company.atlassian.net
export JIRA_USERNAME=your_email@company.com
export JIRA_API_TOKEN=your_api_token
export XRAY_PROJECT_KEY=YOUR_PROJECT
```

### 3. SQL Server Setup
```bash
# Configure SQL Server connection
export USE_SQL_SERVER=true
export SQL_SERVER_CONNECTION="DRIVER={ODBC Driver 17 for SQL Server};SERVER=your_server;DATABASE=your_db;Trusted_Connection=yes;"
```

## 📈 Extending the Demo

### Adding New Scenarios
1. Create new `.feature` files in `features/`
2. Add corresponding step definitions in `features/steps/step_definitions.py`
3. Implement test logic using pytest, Selenium, or Great Expectations

### Custom Gherkin Templates
1. Modify `app/gherkin_generator.py`
2. Add new prompt templates for different scenario types
3. Customize the AWS Bedrock model parameters

### Additional Integrations
1. Add new test frameworks in `app/`
2. Extend Xray integration for more Jira features
3. Add support for other BDD tools (Cucumber, SpecFlow)

## 📚 Documentation

- **Behave**: https://behave.readthedocs.io/
- **Great Expectations**: https://docs.greatexpectations.io/
- **Selenium**: https://selenium-python.readthedocs.io/
- **Streamlit**: https://docs.streamlit.io/
- **Jira Xray**: https://docs.getxray.app/

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**🎉 Happy Testing!** 

This demo shows how modern BDD practices can bridge the gap between business requirements and automated testing, making quality assurance more accessible and efficient.
