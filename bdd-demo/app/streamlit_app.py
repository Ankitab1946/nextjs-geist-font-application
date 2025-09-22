"""Streamlit UI application for BDD Demo project."""

import os
import json
import time
import threading
import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional

# Import our modules
from app.config import Config
from app.gherkin_generator import GherkinGenerator
from app.behave_runner import BehaveRunner, list_features
from app.xray_integration import XrayIntegration
from app.db_utils import get_db_manager
from app.fastapi_mock_api import run_server
from app.utils import setup_logging, save_text_file, get_timestamp

# Setup
logger = setup_logging()
config = Config()

# Page configuration
st.set_page_config(
    page_title="BDD Demo - Gherkin Generator & Test Runner",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f2937;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(90deg, #f3f4f6 0%, #e5e7eb 100%);
        border-radius: 10px;
    }
    
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #374151;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e5e7eb;
    }
    
    .status-success {
        background-color: #d1fae5;
        color: #065f46;
        padding: 0.75rem;
        border-radius: 8px;
        border-left: 4px solid #10b981;
        margin: 1rem 0;
    }
    
    .status-error {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 0.75rem;
        border-radius: 8px;
        border-left: 4px solid #ef4444;
        margin: 1rem 0;
    }
    
    .status-info {
        background-color: #dbeafe;
        color: #1e40af;
        padding: 0.75rem;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
        margin: 1rem 0;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #e5e7eb;
        margin: 1rem 0;
    }
    
    .code-block {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        line-height: 1.5;
        overflow-x: auto;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables."""
    if 'generated_gherkin' not in st.session_state:
        st.session_state.generated_gherkin = ""
    if 'last_test_results' not in st.session_state:
        st.session_state.last_test_results = None
    if 'api_server_running' not in st.session_state:
        st.session_state.api_server_running = False
    if 'xray_upload_result' not in st.session_state:
        st.session_state.xray_upload_result = None

def start_api_server():
    """Start FastAPI server in background thread."""
    if not st.session_state.api_server_running:
        try:
            # Start server in a separate thread
            server_thread = threading.Thread(
                target=run_server,
                args=(config.FASTAPI_HOST, config.FASTAPI_PORT),
                daemon=True
            )
            server_thread.start()
            st.session_state.api_server_running = True
            time.sleep(2)  # Give server time to start
            return True
        except Exception as e:
            logger.error(f"Failed to start API server: {e}")
            return False
    return True

def render_header():
    """Render the main header."""
    st.markdown('<div class="main-header">🧪 BDD Demo - Gherkin Generator & Test Runner</div>', unsafe_allow_html=True)
    
    st.markdown("""
    **Convert English requirements to Gherkin, run BDD tests, and integrate with Jira Xray**
    
    This demo showcases:
    - English to Gherkin conversion using mocked AWS Bedrock
    - BDD test execution with Behave
    - Data validation with Great Expectations
    - UI testing with Selenium
    - Jira Xray integration (mocked)
    """)

def render_sidebar():
    """Render the sidebar with configuration and links."""
    st.sidebar.markdown("## ⚙️ Configuration")
    
    # Database mode toggle
    use_sql_server = st.sidebar.checkbox(
        "Use SQL Server", 
        value=config.USE_SQL_SERVER,
        help="Toggle between SQLite and SQL Server"
    )
    
    # Mock mode toggle
    mock_mode = st.sidebar.checkbox(
        "Mock Mode", 
        value=config.MOCK_MODE,
        help="Use mocked AWS Bedrock and Jira Xray APIs"
    )
    
    # API Server status
    st.sidebar.markdown("## 🌐 API Server")
    if st.session_state.api_server_running:
        st.sidebar.success("✅ FastAPI Server Running")
        st.sidebar.markdown(f"**URL:** http://{config.FASTAPI_HOST}:{config.FASTAPI_PORT}")
    else:
        if st.sidebar.button("🚀 Start API Server"):
            with st.spinner("Starting API server..."):
                if start_api_server():
                    st.sidebar.success("API server started!")
                    st.rerun()
                else:
                    st.sidebar.error("Failed to start API server")
    
    # Quick links
    st.sidebar.markdown("## 🔗 Quick Links")
    if st.session_state.api_server_running:
        st.sidebar.markdown(f"- [Dashboard](http://{config.FASTAPI_HOST}:{config.FASTAPI_PORT}/dashboard)")
        st.sidebar.markdown(f"- [API Health](http://{config.FASTAPI_HOST}:{config.FASTAPI_PORT}/health)")
        st.sidebar.markdown(f"- [Clients API](http://{config.FASTAPI_HOST}:{config.FASTAPI_PORT}/clients)")
    
    # File system links
    st.sidebar.markdown("## 📁 Generated Files")
    if os.path.exists("screenshots"):
        screenshot_count = len([f for f in os.listdir("screenshots") if f.endswith('.png')])
        st.sidebar.markdown(f"- Screenshots: {screenshot_count} files")
    
    if os.path.exists("reports"):
        report_count = len([f for f in os.listdir("reports") if f.endswith('.json')])
        st.sidebar.markdown(f"- Reports: {report_count} files")
    
    if os.path.exists("features"):
        feature_count = len([f for f in os.listdir("features") if f.endswith('.feature')])
        st.sidebar.markdown(f"- Features: {feature_count} files")

def render_gherkin_generator():
    """Render the Gherkin generator section."""
    st.markdown('<div class="section-header">📝 English to Gherkin Conversion</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Input area
        requirement_text = st.text_area(
            "Enter your requirement in plain English:",
            height=150,
            placeholder="Example: I want to validate that the revenue data for Client A is displayed correctly on the dashboard and shows a positive number.",
            help="Describe your testing requirement in natural language"
        )
        
        # Generate button
        if st.button("🔄 Generate Gherkin", type="primary", use_container_width=True):
            if requirement_text.strip():
                with st.spinner("Generating Gherkin using mocked AWS Bedrock..."):
                    generator = GherkinGenerator()
                    result = generator.generate_gherkin(requirement_text)
                    
                    if result['success']:
                        st.session_state.generated_gherkin = result['gherkin_content']
                        
                        st.markdown('<div class="status-success">✅ Gherkin generated successfully!</div>', unsafe_allow_html=True)
                        
                        # Show generation details
                        st.info(f"""
                        **Generated:** {result['feature_filename']}  
                        **Model:** {result.get('model_used', 'Mock Bedrock')}  
                        **Processing Time:** {result.get('processing_time', 0):.2f}s
                        """)
                        
                    else:
                        st.markdown(f'<div class="status-error">❌ Generation failed: {result.get("error", "Unknown error")}</div>', unsafe_allow_html=True)
            else:
                st.warning("Please enter a requirement description.")
    
    with col2:
        # Feature files list
        st.markdown("**Generated Features:**")
        features = list_features()
        
        if features:
            for feature in features[:5]:  # Show latest 5
                st.markdown(f"- {feature['filename']}")
                st.caption(f"Modified: {datetime.fromisoformat(feature['modified_time']).strftime('%Y-%m-%d %H:%M')}")
        else:
            st.info("No feature files generated yet.")
    
    # Display generated Gherkin
    if st.session_state.generated_gherkin:
        st.markdown("**Generated Gherkin:**")
        st.markdown(f'<div class="code-block">{st.session_state.generated_gherkin}</div>', unsafe_allow_html=True)
        
        # Download button
        st.download_button(
            label="📥 Download Feature File",
            data=st.session_state.generated_gherkin,
            file_name=f"generated_feature_{get_timestamp()}.feature",
            mime="text/plain"
        )

def render_test_execution():
    """Render the test execution section."""
    st.markdown('<div class="section-header">🧪 BDD Test Execution</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("**Available Features:**")
        features = list_features()
        
        if features:
            # Feature selection
            selected_features = st.multiselect(
                "Select features to run:",
                options=[f['filename'] for f in features],
                default=[f['filename'] for f in features[:3]],  # Select first 3 by default
                help="Choose which feature files to execute"
            )
            
            # Run tests button
            if st.button("▶️ Run Selected Tests", type="primary", use_container_width=True):
                if selected_features:
                    run_behave_tests(selected_features)
                else:
                    st.warning("Please select at least one feature to run.")
            
            # Run all tests button
            if st.button("🚀 Run All Tests", use_container_width=True):
                run_behave_tests()
        else:
            st.info("No feature files available. Generate some Gherkin first!")
    
    with col2:
        # Test results summary
        if st.session_state.last_test_results:
            render_test_results_summary(st.session_state.last_test_results)

def run_behave_tests(selected_features=None):
    """Run Behave tests and display results."""
    with st.spinner("Running BDD tests..."):
        # Ensure API server is running
        if not st.session_state.api_server_running:
            start_api_server()
        
        runner = BehaveRunner()
        
        if selected_features:
            # Run specific features (this would need implementation in BehaveRunner)
            result = runner.run_all_features()  # For now, run all
        else:
            result = runner.run_all_features()
        
        st.session_state.last_test_results = result
        
        if result['success']:
            st.success("✅ Tests completed successfully!")
        else:
            st.error(f"❌ Tests failed: {result.get('error', 'Unknown error')}")
        
        # Show detailed results
        render_test_results_detailed(result)

def render_test_results_summary(results: Dict[str, Any]):
    """Render test results summary."""
    st.markdown("**Latest Test Results:**")
    
    stats = results.get('statistics', {})
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Scenarios", stats.get('total_scenarios', 0))
    
    with col2:
        st.metric("Passed", stats.get('passed_scenarios', 0))
    
    with col3:
        st.metric("Failed", stats.get('failed_scenarios', 0))
    
    with col4:
        success_rate = stats.get('success_rate', 0)
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    # Status indicator
    if results.get('success', False):
        st.markdown('<div class="status-success">✅ All tests passed</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-error">❌ Some tests failed</div>', unsafe_allow_html=True)

def render_test_results_detailed(results: Dict[str, Any]):
    """Render detailed test results."""
    st.markdown("### 📊 Detailed Test Results")
    
    # Execution info
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"""
        **Execution Time:** {results.get('execution_time', 'N/A')}  
        **Return Code:** {results.get('return_code', 'N/A')}  
        **Timestamp:** {results.get('timestamp', 'N/A')}
        """)
    
    with col2:
        # Files generated
        cucumber_file = results.get('cucumber_json_file', '')
        if cucumber_file and os.path.exists(cucumber_file):
            st.success(f"📄 Cucumber report: {os.path.basename(cucumber_file)}")
        
        junit_file = results.get('junit_xml_file', '')
        if junit_file and os.path.exists(junit_file):
            st.success(f"📄 JUnit report: {os.path.basename(junit_file)}")
    
    # Scenario results
    scenarios = results.get('scenarios', [])
    if scenarios:
        st.markdown("**Scenario Results:**")
        
        for scenario in scenarios:
            status_icon = "✅" if scenario['status'] == 'passed' else "❌"
            
            with st.expander(f"{status_icon} {scenario['name']} ({scenario['status'].upper()})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Feature:** {scenario['feature_name']}")
                    st.write(f"**Duration:** {scenario['duration']:.3f}s")
                    st.write(f"**Steps:** {scenario['total_steps']} total, {scenario['passed_steps']} passed, {scenario['failed_steps']} failed")
                
                with col2:
                    # Step details
                    for step in scenario.get('steps', []):
                        step_icon = "✅" if step['status'] == 'passed' else "❌" if step['status'] == 'failed' else "⏭️"
                        st.write(f"{step_icon} {step['keyword']}{step['name']}")
                        
                        if step.get('error_message'):
                            st.error(f"Error: {step['error_message']}")
    
    # Console output
    if results.get('stdout') or results.get('stderr'):
        with st.expander("📋 Console Output"):
            if results.get('stdout'):
                st.text("STDOUT:")
                st.code(results['stdout'], language='text')
            
            if results.get('stderr'):
                st.text("STDERR:")
                st.code(results['stderr'], language='text')

def render_xray_integration():
    """Render Jira Xray integration section."""
    st.markdown('<div class="section-header">🔗 Jira Xray Integration</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Upload section
        st.markdown("**Upload Test Results to Jira Xray:**")
        
        # Check for available Cucumber reports
        reports_dir = "reports"
        cucumber_reports = []
        
        if os.path.exists(reports_dir):
            cucumber_reports = [f for f in os.listdir(reports_dir) if f.startswith('cucumber_report_') and f.endswith('.json')]
        
        if cucumber_reports:
            selected_report = st.selectbox(
                "Select Cucumber report to upload:",
                options=cucumber_reports,
                help="Choose a Cucumber JSON report to upload to Xray"
            )
            
            if st.button("📤 Upload to Xray", type="primary", use_container_width=True):
                upload_to_xray(os.path.join(reports_dir, selected_report))
        else:
            st.info("No Cucumber reports available. Run some tests first!")
        
        # Test plan creation
        st.markdown("**Create Test Plan:**")
        
        plan_name = st.text_input("Test Plan Name:", value=f"BDD Demo Test Plan {get_timestamp()}")
        plan_description = st.text_area("Description:", value="Automated test plan created from BDD Demo")
        
        if st.button("📋 Create Test Plan", use_container_width=True):
            create_xray_test_plan(plan_name, plan_description)
    
    with col2:
        # Xray results
        if st.session_state.xray_upload_result:
            render_xray_results(st.session_state.xray_upload_result)

def upload_to_xray(report_path: str):
    """Upload Cucumber report to Xray."""
    with st.spinner("Uploading to Jira Xray..."):
        xray = XrayIntegration()
        result = xray.upload_cucumber_results(report_path)
        
        st.session_state.xray_upload_result = result
        
        if result['success']:
            st.success("✅ Successfully uploaded to Xray!")
        else:
            st.error(f"❌ Upload failed: {result.get('error', 'Unknown error')}")

def create_xray_test_plan(name: str, description: str):
    """Create test plan in Xray."""
    with st.spinner("Creating test plan in Xray..."):
        xray = XrayIntegration()
        result = xray.create_test_plan(name, description)
        
        if result['success']:
            st.success(f"✅ Test plan created: {result['test_plan_key']}")
            st.info(f"**URL:** {result['test_plan_url']}")
        else:
            st.error(f"❌ Test plan creation failed: {result.get('error', 'Unknown error')}")

def render_xray_results(result: Dict[str, Any]):
    """Render Xray upload results."""
    st.markdown("**Xray Upload Results:**")
    
    if result['success']:
        st.markdown('<div class="status-success">✅ Upload Successful</div>', unsafe_allow_html=True)
        
        # Key information
        st.info(f"""
        **Test Execution:** {result.get('test_execution_key', 'N/A')}  
        **Test Plan:** {result.get('test_plan_key', 'N/A')}  
        **Upload Time:** {result.get('upload_timestamp', 'N/A')}
        """)
        
        # Statistics
        stats = result.get('statistics', {})
        if stats:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Scenarios", stats.get('total_scenarios', 0))
            
            with col2:
                st.metric("Passed", stats.get('passed_scenarios', 0))
            
            with col3:
                st.metric("Success Rate", f"{stats.get('success_rate', 0):.1f}%")
        
        # Links
        st.markdown("**Jira Links:**")
        if result.get('test_execution_url'):
            st.markdown(f"- [Test Execution]({result['test_execution_url']})")
        if result.get('test_plan_url'):
            st.markdown(f"- [Test Plan]({result['test_plan_url']})")
    
    else:
        st.markdown(f'<div class="status-error">❌ Upload Failed: {result.get("error", "Unknown error")}</div>', unsafe_allow_html=True)

def render_reports_download():
    """Render reports download section."""
    st.markdown('<div class="section-header">📥 Download Reports</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Test Reports:**")
        
        reports_dir = "reports"
        if os.path.exists(reports_dir):
            report_files = [f for f in os.listdir(reports_dir) if f.endswith(('.json', '.xml', '.html'))]
            
            for report_file in report_files[:5]:  # Show latest 5
                file_path = os.path.join(reports_dir, report_file)
                
                with open(file_path, 'rb') as f:
                    st.download_button(
                        label=f"📄 {report_file}",
                        data=f.read(),
                        file_name=report_file,
                        mime="application/octet-stream"
                    )
    
    with col2:
        st.markdown("**Screenshots:**")
        
        screenshots_dir = "screenshots"
        if os.path.exists(screenshots_dir):
            screenshot_files = [f for f in os.listdir(screenshots_dir) if f.endswith('.png')]
            
            for screenshot_file in screenshot_files[:5]:  # Show latest 5
                file_path = os.path.join(screenshots_dir, screenshot_file)
                
                with open(file_path, 'rb') as f:
                    st.download_button(
                        label=f"🖼️ {screenshot_file}",
                        data=f.read(),
                        file_name=screenshot_file,
                        mime="image/png"
                    )
    
    with col3:
        st.markdown("**Data Docs:**")
        
        data_docs_dir = "data/ge_data_docs"
        if os.path.exists(data_docs_dir):
            doc_files = [f for f in os.listdir(data_docs_dir) if f.endswith('.html')]
            
            for doc_file in doc_files[:5]:  # Show latest 5
                file_path = os.path.join(data_docs_dir, doc_file)
                
                with open(file_path, 'rb') as f:
                    st.download_button(
                        label=f"📊 {doc_file}",
                        data=f.read(),
                        file_name=doc_file,
                        mime="text/html"
                    )

def main():
    """Main Streamlit application."""
    initialize_session_state()
    
    # Render UI sections
    render_header()
    render_sidebar()
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔄 Generate Gherkin", "🧪 Run Tests", "🔗 Xray Integration", "📥 Downloads"])
    
    with tab1:
        render_gherkin_generator()
    
    with tab2:
        render_test_execution()
    
    with tab3:
        render_xray_integration()
    
    with tab4:
        render_reports_download()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6b7280; font-size: 0.9rem;">
        🧪 BDD Demo Project - Convert English to Gherkin, Run Tests, Integrate with Xray<br>
        Built with Streamlit, Behave, Great Expectations, Selenium, and mocked AWS Bedrock/Jira Xray
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
