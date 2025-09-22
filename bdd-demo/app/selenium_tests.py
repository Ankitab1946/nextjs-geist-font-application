"""Selenium UI testing module for BDD scenarios."""

import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from app.config import Config
from app.utils import ensure_directory_exists, sanitize_filename

logger = logging.getLogger(__name__)

class SeleniumUITester:
    """Selenium-based UI testing for BDD scenarios."""
    
    def __init__(self):
        self.config = Config()
        self.driver = None
        self.screenshots_dir = self.config.SCREENSHOTS_DIR
        ensure_directory_exists(self.screenshots_dir)
        
    def setup_driver(self) -> bool:
        """Set up Chrome WebDriver with appropriate options."""
        try:
            chrome_options = Options()
            
            if self.config.SELENIUM_HEADLESS:
                chrome_options.add_argument("--headless")
            
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")  # Speed up loading
            
            # Use ChromeDriverManager to automatically manage driver
            service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(self.config.SELENIUM_TIMEOUT)
            
            logger.info("Chrome WebDriver initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup WebDriver: {e}")
            return False
    
    def teardown_driver(self):
        """Close and quit the WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed successfully")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")
            finally:
                self.driver = None
    
    def take_screenshot(self, name: str, description: str = "") -> str:
        """Take a screenshot and save it with timestamp."""
        try:
            if not self.driver:
                logger.error("WebDriver not initialized")
                return ""
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{sanitize_filename(name)}_{timestamp}.png"
            filepath = os.path.join(self.screenshots_dir, filename)
            
            self.driver.save_screenshot(filepath)
            
            logger.info(f"Screenshot saved: {filepath}")
            
            # Also save screenshot metadata
            metadata = {
                "filename": filename,
                "filepath": filepath,
                "timestamp": timestamp,
                "description": description,
                "url": self.driver.current_url,
                "title": self.driver.title,
                "window_size": self.driver.get_window_size()
            }
            
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return ""
    
    def validate_dashboard_page(self, url: str) -> Dict[str, Any]:
        """Validate the dashboard page and look for Client A revenue."""
        result = {
            "success": False,
            "client_a_found": False,
            "revenue_value": None,
            "revenue_valid": False,
            "screenshots": [],
            "errors": [],
            "execution_time": 0
        }
        
        start_time = time.time()
        
        try:
            if not self.driver:
                if not self.setup_driver():
                    result["errors"].append("Failed to setup WebDriver")
                    return result
            
            logger.info(f"Navigating to dashboard: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, self.config.SELENIUM_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Take initial screenshot
            screenshot_path = self.take_screenshot("dashboard_loaded", "Dashboard page loaded")
            if screenshot_path:
                result["screenshots"].append(screenshot_path)
            
            # Wait for clients grid to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "clientsGrid"))
                )
                
                # Give some time for JavaScript to populate the grid
                time.sleep(2)
                
            except TimeoutException:
                result["errors"].append("Clients grid not found or not loaded")
                screenshot_path = self.take_screenshot("grid_not_found", "Clients grid not found")
                if screenshot_path:
                    result["screenshots"].append(screenshot_path)
                return result
            
            # Look for Client A
            client_a_found = False
            revenue_value = None
            
            try:
                # Find all client cards
                client_cards = self.driver.find_elements(By.CLASS_NAME, "client-card")
                logger.info(f"Found {len(client_cards)} client cards")
                
                for card in client_cards:
                    try:
                        # Look for client name
                        name_element = card.find_element(By.CLASS_NAME, "client-name")
                        client_name = name_element.text.strip()
                        
                        if "Client A" in client_name:
                            client_a_found = True
                            logger.info("Client A found!")
                            
                            # Look for revenue value
                            revenue_element = card.find_element(By.CLASS_NAME, "revenue")
                            revenue_text = revenue_element.text.strip()
                            
                            # Extract numeric value from revenue text (e.g., "$150,000.50")
                            import re
                            revenue_match = re.search(r'[\d,]+\.?\d*', revenue_text.replace(',', ''))
                            if revenue_match:
                                revenue_value = float(revenue_match.group())
                                logger.info(f"Client A revenue: {revenue_value}")
                            
                            break
                            
                    except NoSuchElementException as e:
                        logger.warning(f"Element not found in client card: {e}")
                        continue
                
                result["client_a_found"] = client_a_found
                result["revenue_value"] = revenue_value
                
                # Validate revenue (should be positive number)
                if revenue_value is not None:
                    result["revenue_valid"] = revenue_value > 0
                    logger.info(f"Revenue validation: {result['revenue_valid']} (value: {revenue_value})")
                
                # Take screenshot after validation
                screenshot_name = "client_a_found" if client_a_found else "client_a_not_found"
                screenshot_path = self.take_screenshot(screenshot_name, f"Client A validation result")
                if screenshot_path:
                    result["screenshots"].append(screenshot_path)
                
                # Overall success
                result["success"] = client_a_found and result["revenue_valid"]
                
            except Exception as e:
                error_msg = f"Error during client validation: {e}"
                logger.error(error_msg)
                result["errors"].append(error_msg)
                
                screenshot_path = self.take_screenshot("validation_error", "Error during validation")
                if screenshot_path:
                    result["screenshots"].append(screenshot_path)
            
        except TimeoutException:
            error_msg = f"Page load timeout for URL: {url}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
            
            screenshot_path = self.take_screenshot("page_timeout", "Page load timeout")
            if screenshot_path:
                result["screenshots"].append(screenshot_path)
            
        except Exception as e:
            error_msg = f"Unexpected error during UI validation: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
            
            screenshot_path = self.take_screenshot("unexpected_error", "Unexpected error")
            if screenshot_path:
                result["screenshots"].append(screenshot_path)
        
        finally:
            result["execution_time"] = round(time.time() - start_time, 2)
            logger.info(f"UI validation completed in {result['execution_time']} seconds")
        
        return result
    
    def validate_page_elements(self, url: str, expected_elements: list) -> Dict[str, Any]:
        """Validate that expected elements are present on the page."""
        result = {
            "success": False,
            "elements_found": {},
            "missing_elements": [],
            "screenshots": [],
            "errors": [],
            "execution_time": 0
        }
        
        start_time = time.time()
        
        try:
            if not self.driver:
                if not self.setup_driver():
                    result["errors"].append("Failed to setup WebDriver")
                    return result
            
            logger.info(f"Navigating to page: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, self.config.SELENIUM_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Take initial screenshot
            screenshot_path = self.take_screenshot("page_loaded", "Page loaded for element validation")
            if screenshot_path:
                result["screenshots"].append(screenshot_path)
            
            # Check each expected element
            for element_info in expected_elements:
                element_name = element_info.get("name", "unknown")
                selector_type = element_info.get("type", "id")  # id, class, tag, xpath
                selector_value = element_info.get("value", "")
                
                try:
                    if selector_type == "id":
                        element = self.driver.find_element(By.ID, selector_value)
                    elif selector_type == "class":
                        element = self.driver.find_element(By.CLASS_NAME, selector_value)
                    elif selector_type == "tag":
                        element = self.driver.find_element(By.TAG_NAME, selector_value)
                    elif selector_type == "xpath":
                        element = self.driver.find_element(By.XPATH, selector_value)
                    else:
                        raise ValueError(f"Unsupported selector type: {selector_type}")
                    
                    result["elements_found"][element_name] = {
                        "found": True,
                        "visible": element.is_displayed(),
                        "text": element.text[:100] if element.text else "",
                        "tag": element.tag_name
                    }
                    
                    logger.info(f"Element '{element_name}' found and {'visible' if element.is_displayed() else 'hidden'}")
                    
                except NoSuchElementException:
                    result["elements_found"][element_name] = {"found": False}
                    result["missing_elements"].append(element_name)
                    logger.warning(f"Element '{element_name}' not found")
                
                except Exception as e:
                    result["elements_found"][element_name] = {"found": False, "error": str(e)}
                    result["missing_elements"].append(element_name)
                    logger.error(f"Error checking element '{element_name}': {e}")
            
            # Take final screenshot
            screenshot_path = self.take_screenshot("elements_validated", "Element validation completed")
            if screenshot_path:
                result["screenshots"].append(screenshot_path)
            
            # Overall success (all elements found and visible)
            all_found = all(
                info.get("found", False) and info.get("visible", False) 
                for info in result["elements_found"].values()
            )
            result["success"] = all_found and len(result["missing_elements"]) == 0
            
        except Exception as e:
            error_msg = f"Error during element validation: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
            
            screenshot_path = self.take_screenshot("element_validation_error", "Error during element validation")
            if screenshot_path:
                result["screenshots"].append(screenshot_path)
        
        finally:
            result["execution_time"] = round(time.time() - start_time, 2)
            logger.info(f"Element validation completed in {result['execution_time']} seconds")
        
        return result
    
    def get_page_source(self) -> Optional[str]:
        """Get the current page source."""
        if self.driver:
            return self.driver.page_source
        return None
    
    def get_current_url(self) -> Optional[str]:
        """Get the current URL."""
        if self.driver:
            return self.driver.current_url
        return None

# Convenience functions for easy access
def validate_dashboard(url: str = "http://127.0.0.1:8001/dashboard") -> Dict[str, Any]:
    """Quick dashboard validation."""
    tester = SeleniumUITester()
    try:
        return tester.validate_dashboard_page(url)
    finally:
        tester.teardown_driver()

def validate_elements(url: str, elements: list) -> Dict[str, Any]:
    """Quick element validation."""
    tester = SeleniumUITester()
    try:
        return tester.validate_page_elements(url, elements)
    finally:
        tester.teardown_driver()
