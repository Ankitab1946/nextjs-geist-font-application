"""Great Expectations data quality checks module."""

import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import pandas as pd
from app.config import Config
from app.utils import ensure_directory_exists, save_json_file

logger = logging.getLogger(__name__)

class DataQualityChecker:
    """Data quality checker using Great Expectations concepts (simplified mock)."""
    
    def __init__(self):
        self.config = Config()
        self.data_docs_dir = "data/ge_data_docs"
        ensure_directory_exists(self.data_docs_dir)
        
    def create_expectation_suite(self, suite_name: str) -> Dict[str, Any]:
        """Create a mock expectation suite."""
        suite = {
            "expectation_suite_name": suite_name,
            "ge_cloud_id": None,
            "expectations": [],
            "data_asset_type": "Dataset",
            "meta": {
                "great_expectations_version": "0.18.8"
            }
        }
        return suite
    
    def add_expectation(self, suite: Dict[str, Any], expectation_type: str, 
                       column: str = None, **kwargs) -> Dict[str, Any]:
        """Add an expectation to the suite."""
        expectation = {
            "expectation_type": expectation_type,
            "meta": {}
        }
        
        if column:
            expectation["kwargs"] = {"column": column, **kwargs}
        else:
            expectation["kwargs"] = kwargs
            
        suite["expectations"].append(expectation)
        return suite
    
    def validate_api_data(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate API data against expectations."""
        try:
            # Convert API data to DataFrame for validation
            if isinstance(api_data, dict) and 'data' in api_data:
                df = pd.DataFrame(api_data['data'])
            elif isinstance(api_data, list):
                df = pd.DataFrame(api_data)
            else:
                df = pd.DataFrame([api_data])
            
            # Create expectation suite for API data
            suite = self.create_expectation_suite("api_data_validation")
            
            # Add expectations based on data structure
            results = []
            
            for column in df.columns:
                if df[column].dtype in ['int64', 'float64']:
                    # Numeric column expectations
                    result = self._validate_numeric_column(df, column)
                    results.append(result)
                elif df[column].dtype == 'object':
                    # String column expectations
                    result = self._validate_string_column(df, column)
                    results.append(result)
            
            # Overall validation result
            all_passed = all(r['success'] for r in results)
            
            validation_result = {
                "success": all_passed,
                "statistics": {
                    "evaluated_expectations": len(results),
                    "successful_expectations": sum(1 for r in results if r['success']),
                    "unsuccessful_expectations": sum(1 for r in results if not r['success']),
                    "success_percent": (sum(1 for r in results if r['success']) / len(results) * 100) if results else 0
                },
                "results": results,
                "meta": {
                    "validation_time": pd.Timestamp.now().isoformat(),
                    "expectation_suite_name": "api_data_validation"
                }
            }
            
            # Save validation results
            self._save_validation_results(validation_result)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"API data validation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "statistics": {"evaluated_expectations": 0, "successful_expectations": 0}
            }
    
    def _validate_numeric_column(self, df: pd.DataFrame, column: str) -> Dict[str, Any]:
        """Validate numeric column expectations."""
        try:
            col_data = df[column]
            
            # Check for null values
            null_count = col_data.isnull().sum()
            has_nulls = null_count > 0
            
            # Check value ranges (example: should be positive for revenue-like fields)
            if 'revenue' in column.lower() or 'amount' in column.lower():
                min_value = col_data.min()
                all_positive = min_value >= 0
            else:
                all_positive = True  # Not applicable
            
            # Check for reasonable ranges (example: revenue should be < 1M)
            if 'revenue' in column.lower():
                max_value = col_data.max()
                reasonable_max = max_value <= 1000000
            else:
                reasonable_max = True  # Not applicable
            
            success = not has_nulls and all_positive and reasonable_max
            
            return {
                "expectation_config": {
                    "expectation_type": "expect_column_values_to_be_between",
                    "kwargs": {"column": column, "min_value": 0, "max_value": 1000000}
                },
                "success": success,
                "result": {
                    "observed_value": {
                        "min": float(col_data.min()),
                        "max": float(col_data.max()),
                        "null_count": int(null_count)
                    },
                    "details": {
                        "has_nulls": has_nulls,
                        "all_positive": all_positive,
                        "reasonable_max": reasonable_max
                    }
                }
            }
            
        except Exception as e:
            return {
                "expectation_config": {"expectation_type": "expect_column_values_to_be_between"},
                "success": False,
                "result": {"error": str(e)}
            }
    
    def _validate_string_column(self, df: pd.DataFrame, column: str) -> Dict[str, Any]:
        """Validate string column expectations."""
        try:
            col_data = df[column]
            
            # Check for null values
            null_count = col_data.isnull().sum()
            has_nulls = null_count > 0
            
            # Check for empty strings
            empty_count = (col_data == '').sum()
            has_empty = empty_count > 0
            
            # Check string length (should be reasonable)
            if not col_data.empty:
                max_length = col_data.astype(str).str.len().max()
                reasonable_length = max_length <= 255
            else:
                reasonable_length = True
            
            success = not has_nulls and not has_empty and reasonable_length
            
            return {
                "expectation_config": {
                    "expectation_type": "expect_column_values_to_not_be_null",
                    "kwargs": {"column": column}
                },
                "success": success,
                "result": {
                    "observed_value": {
                        "null_count": int(null_count),
                        "empty_count": int(empty_count),
                        "max_length": int(max_length) if not col_data.empty else 0
                    },
                    "details": {
                        "has_nulls": has_nulls,
                        "has_empty": has_empty,
                        "reasonable_length": reasonable_length
                    }
                }
            }
            
        except Exception as e:
            return {
                "expectation_config": {"expectation_type": "expect_column_values_to_not_be_null"},
                "success": False,
                "result": {"error": str(e)}
            }
    
    def validate_database_table(self, table_name: str, expected_count: int = None) -> Dict[str, Any]:
        """Validate database table data quality."""
        try:
            from app.db_utils import get_db_manager
            
            db = get_db_manager()
            
            # Get table info
            table_info = db.get_table_info(table_name)
            if not table_info:
                return {
                    "success": False,
                    "error": f"Table {table_name} not found or inaccessible"
                }
            
            results = []
            
            # Validate row count if expected count is provided
            if expected_count is not None:
                actual_count = table_info['row_count']
                count_match = actual_count == expected_count
                
                results.append({
                    "expectation_config": {
                        "expectation_type": "expect_table_row_count_to_equal",
                        "kwargs": {"value": expected_count}
                    },
                    "success": count_match,
                    "result": {
                        "observed_value": actual_count,
                        "expected_value": expected_count
                    }
                })
            
            # Validate that table has data
            has_data = table_info['row_count'] > 0
            results.append({
                "expectation_config": {
                    "expectation_type": "expect_table_row_count_to_be_between",
                    "kwargs": {"min_value": 1}
                },
                "success": has_data,
                "result": {
                    "observed_value": table_info['row_count']
                }
            })
            
            all_passed = all(r['success'] for r in results)
            
            validation_result = {
                "success": all_passed,
                "statistics": {
                    "evaluated_expectations": len(results),
                    "successful_expectations": sum(1 for r in results if r['success']),
                    "unsuccessful_expectations": sum(1 for r in results if not r['success']),
                    "success_percent": (sum(1 for r in results if r['success']) / len(results) * 100) if results else 0
                },
                "results": results,
                "meta": {
                    "validation_time": pd.Timestamp.now().isoformat(),
                    "table_name": table_name,
                    "table_info": table_info
                }
            }
            
            db.disconnect()
            return validation_result
            
        except Exception as e:
            logger.error(f"Database table validation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "statistics": {"evaluated_expectations": 0, "successful_expectations": 0}
            }
    
    def _save_validation_results(self, validation_result: Dict[str, Any]):
        """Save validation results and generate data docs."""
        try:
            # Save validation results as JSON
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            results_file = f"{self.data_docs_dir}/validation_results_{timestamp}.json"
            save_json_file(validation_result, results_file)
            
            # Generate simple HTML data docs
            self._generate_data_docs(validation_result, timestamp)
            
        except Exception as e:
            logger.error(f"Failed to save validation results: {e}")
    
    def _generate_data_docs(self, validation_result: Dict[str, Any], timestamp: str):
        """Generate simple HTML data docs."""
        try:
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Data Quality Validation Results</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .success {{ color: green; }}
        .failure {{ color: red; }}
        .stats {{ background-color: #f9f9f9; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .expectation {{ margin: 10px 0; padding: 10px; border-left: 3px solid #ccc; }}
        .expectation.success {{ border-left-color: green; }}
        .expectation.failure {{ border-left-color: red; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Data Quality Validation Results</h1>
        <p>Generated: {validation_result.get('meta', {}).get('validation_time', timestamp)}</p>
        <p>Overall Status: <span class="{'success' if validation_result['success'] else 'failure'}">
            {'PASSED' if validation_result['success'] else 'FAILED'}
        </span></p>
    </div>
    
    <div class="stats">
        <h2>Statistics</h2>
        <p>Evaluated Expectations: {validation_result['statistics']['evaluated_expectations']}</p>
        <p>Successful: {validation_result['statistics']['successful_expectations']}</p>
        <p>Failed: {validation_result['statistics']['unsuccessful_expectations']}</p>
        <p>Success Rate: {validation_result['statistics']['success_percent']:.1f}%</p>
    </div>
    
    <h2>Expectation Results</h2>
"""
            
            for result in validation_result.get('results', []):
                status_class = 'success' if result['success'] else 'failure'
                status_text = 'PASSED' if result['success'] else 'FAILED'
                
                html_content += f"""
    <div class="expectation {status_class}">
        <h3>{result['expectation_config']['expectation_type']}</h3>
        <p>Status: <span class="{status_class}">{status_text}</span></p>
        <p>Details: {json.dumps(result.get('result', {}), indent=2)}</p>
    </div>
"""
            
            html_content += """
</body>
</html>
"""
            
            html_file = f"{self.data_docs_dir}/data_docs_{timestamp}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Data docs generated: {html_file}")
            
        except Exception as e:
            logger.error(f"Failed to generate data docs: {e}")
    
    def get_latest_validation_results(self) -> Optional[Dict[str, Any]]:
        """Get the latest validation results."""
        try:
            import os
            import glob
            
            # Find the latest validation results file
            pattern = f"{self.data_docs_dir}/validation_results_*.json"
            files = glob.glob(pattern)
            
            if not files:
                return None
            
            latest_file = max(files, key=os.path.getctime)
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Failed to get latest validation results: {e}")
            return None

# Convenience functions
def validate_api_data(api_data: Dict[str, Any]) -> Dict[str, Any]:
    """Quick API data validation."""
    checker = DataQualityChecker()
    return checker.validate_api_data(api_data)

def validate_table(table_name: str, expected_count: int = None) -> Dict[str, Any]:
    """Quick table validation."""
    checker = DataQualityChecker()
    return checker.validate_database_table(table_name, expected_count)
