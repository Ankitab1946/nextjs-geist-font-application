"""Behave runner module for executing BDD tests programmatically."""

import os
import json
import subprocess
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from app.config import Config
from app.utils import setup_logging, save_json_file, TestMetadata

logger = setup_logging()

class BehaveRunner:
    """Behave test runner for executing BDD scenarios."""
    
    def __init__(self):
        self.config = Config()
        self.features_dir = self.config.FEATURES_DIR
        self.reports_dir = self.config.REPORTS_DIR
        self.metadata = TestMetadata()
        
    def run_all_features(self) -> Dict[str, Any]:
        """Run all feature files in the features directory."""
        try:
            logger.info("Starting Behave test execution for all features")
            self.metadata = TestMetadata()
            
            # Ensure directories exist
            os.makedirs(self.reports_dir, exist_ok=True)
            
            # Generate timestamp for this test run
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Prepare Behave command
            cucumber_json_file = os.path.join(self.reports_dir, f"cucumber_report_{timestamp}.json")
            junit_xml_file = os.path.join(self.reports_dir, f"junit_report_{timestamp}.xml")
            
            behave_cmd = [
                "behave",
                self.features_dir,
                "--format=json",
                f"--outfile={cucumber_json_file}",
                "--format=junit",
                f"--outfile={junit_xml_file}",
                "--format=pretty",
                "--no-capture",
                "--no-capture-stderr"
            ]
            
            logger.info(f"Executing command: {' '.join(behave_cmd)}")
            
            # Execute Behave
            result = subprocess.run(
                behave_cmd,
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            self.metadata.mark_complete()
            
            # Parse results
            execution_result = self._parse_behave_results(
                result, cucumber_json_file, junit_xml_file, timestamp
            )
            
            # Save execution metadata
            self.metadata.test_results = execution_result
            metadata_file = os.path.join(self.reports_dir, f"test_metadata_{timestamp}.json")
            save_json_file(self.metadata.to_dict(), metadata_file)
            
            logger.info(f"Behave execution completed. Results saved to {cucumber_json_file}")
            return execution_result
            
        except Exception as e:
            logger.error(f"Error running Behave tests: {e}")
            return {
                'success': False,
                'error': str(e),
                'execution_time': self.metadata.get_duration(),
                'timestamp': datetime.now().isoformat()
            }
    
    def run_specific_feature(self, feature_file: str) -> Dict[str, Any]:
        """Run a specific feature file."""
        try:
            feature_path = os.path.join(self.features_dir, feature_file)
            
            if not os.path.exists(feature_path):
                return {
                    'success': False,
                    'error': f"Feature file not found: {feature_path}",
                    'feature_file': feature_file
                }
            
            logger.info(f"Running specific feature: {feature_file}")
            self.metadata = TestMetadata()
            
            # Generate timestamp for this test run
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Prepare Behave command for specific feature
            cucumber_json_file = os.path.join(self.reports_dir, f"cucumber_report_{feature_file}_{timestamp}.json")
            
            behave_cmd = [
                "behave",
                feature_path,
                "--format=json",
                f"--outfile={cucumber_json_file}",
                "--format=pretty",
                "--no-capture"
            ]
            
            logger.info(f"Executing command: {' '.join(behave_cmd)}")
            
            # Execute Behave
            result = subprocess.run(
                behave_cmd,
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            self.metadata.mark_complete()
            
            # Parse results
            execution_result = self._parse_behave_results(
                result, cucumber_json_file, None, timestamp, feature_file
            )
            
            return execution_result
            
        except Exception as e:
            logger.error(f"Error running feature {feature_file}: {e}")
            return {
                'success': False,
                'error': str(e),
                'feature_file': feature_file,
                'execution_time': self.metadata.get_duration(),
                'timestamp': datetime.now().isoformat()
            }
    
    def _parse_behave_results(self, subprocess_result, cucumber_json_file: str, 
                             junit_xml_file: str = None, timestamp: str = "", 
                             feature_file: str = None) -> Dict[str, Any]:
        """Parse Behave execution results."""
        try:
            # Basic execution info
            execution_result = {
                'success': subprocess_result.returncode == 0,
                'return_code': subprocess_result.returncode,
                'stdout': subprocess_result.stdout,
                'stderr': subprocess_result.stderr,
                'execution_time': self.metadata.get_duration(),
                'timestamp': timestamp,
                'cucumber_json_file': cucumber_json_file,
                'junit_xml_file': junit_xml_file,
                'feature_file': feature_file,
                'scenarios': [],
                'statistics': {
                    'total_scenarios': 0,
                    'passed_scenarios': 0,
                    'failed_scenarios': 0,
                    'skipped_scenarios': 0,
                    'total_steps': 0,
                    'passed_steps': 0,
                    'failed_steps': 0,
                    'skipped_steps': 0
                }
            }
            
            # Parse Cucumber JSON if it exists
            if os.path.exists(cucumber_json_file):
                try:
                    with open(cucumber_json_file, 'r', encoding='utf-8') as f:
                        cucumber_data = json.load(f)
                    
                    execution_result['cucumber_data'] = cucumber_data
                    
                    # Parse scenarios and steps
                    for feature in cucumber_data:
                        feature_name = feature.get('name', 'Unknown Feature')
                        
                        for element in feature.get('elements', []):
                            if element.get('type') == 'scenario':
                                scenario_info = self._parse_scenario(element, feature_name)
                                execution_result['scenarios'].append(scenario_info)
                                
                                # Update statistics
                                execution_result['statistics']['total_scenarios'] += 1
                                if scenario_info['status'] == 'passed':
                                    execution_result['statistics']['passed_scenarios'] += 1
                                elif scenario_info['status'] == 'failed':
                                    execution_result['statistics']['failed_scenarios'] += 1
                                else:
                                    execution_result['statistics']['skipped_scenarios'] += 1
                                
                                # Step statistics
                                execution_result['statistics']['total_steps'] += scenario_info['total_steps']
                                execution_result['statistics']['passed_steps'] += scenario_info['passed_steps']
                                execution_result['statistics']['failed_steps'] += scenario_info['failed_steps']
                                execution_result['statistics']['skipped_steps'] += scenario_info['skipped_steps']
                    
                    # Calculate success rate
                    total_scenarios = execution_result['statistics']['total_scenarios']
                    if total_scenarios > 0:
                        success_rate = (execution_result['statistics']['passed_scenarios'] / total_scenarios) * 100
                        execution_result['statistics']['success_rate'] = round(success_rate, 2)
                    else:
                        execution_result['statistics']['success_rate'] = 0
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing Cucumber JSON: {e}")
                    execution_result['json_parse_error'] = str(e)
            
            return execution_result
            
        except Exception as e:
            logger.error(f"Error parsing Behave results: {e}")
            return {
                'success': False,
                'error': f"Result parsing error: {e}",
                'return_code': subprocess_result.returncode if subprocess_result else -1,
                'execution_time': self.metadata.get_duration(),
                'timestamp': timestamp
            }
    
    def _parse_scenario(self, scenario_element: Dict, feature_name: str) -> Dict[str, Any]:
        """Parse individual scenario results."""
        scenario_info = {
            'name': scenario_element.get('name', 'Unknown Scenario'),
            'feature_name': feature_name,
            'status': 'unknown',
            'total_steps': 0,
            'passed_steps': 0,
            'failed_steps': 0,
            'skipped_steps': 0,
            'duration': 0,
            'steps': [],
            'tags': scenario_element.get('tags', []),
            'location': scenario_element.get('location', {})
        }
        
        # Analyze steps
        all_steps_passed = True
        total_duration = 0
        
        for step in scenario_element.get('steps', []):
            step_result = step.get('result', {})
            step_status = step_result.get('status', 'unknown')
            step_duration = step_result.get('duration', 0)
            
            step_info = {
                'keyword': step.get('keyword', ''),
                'name': step.get('name', ''),
                'status': step_status,
                'duration': step_duration,
                'error_message': step_result.get('error_message', ''),
                'location': step.get('location', {})
            }
            
            scenario_info['steps'].append(step_info)
            scenario_info['total_steps'] += 1
            total_duration += step_duration
            
            if step_status == 'passed':
                scenario_info['passed_steps'] += 1
            elif step_status == 'failed':
                scenario_info['failed_steps'] += 1
                all_steps_passed = False
            else:
                scenario_info['skipped_steps'] += 1
                all_steps_passed = False
        
        # Determine overall scenario status
        if all_steps_passed and scenario_info['total_steps'] > 0:
            scenario_info['status'] = 'passed'
        elif scenario_info['failed_steps'] > 0:
            scenario_info['status'] = 'failed'
        else:
            scenario_info['status'] = 'skipped'
        
        scenario_info['duration'] = total_duration
        
        return scenario_info
    
    def list_available_features(self) -> List[Dict[str, Any]]:
        """List all available feature files."""
        try:
            features = []
            
            if not os.path.exists(self.features_dir):
                return features
            
            for filename in os.listdir(self.features_dir):
                if filename.endswith('.feature'):
                    filepath = os.path.join(self.features_dir, filename)
                    
                    # Get file info
                    stat = os.stat(filepath)
                    
                    # Try to read feature name from file
                    feature_name = filename
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            first_line = f.readline().strip()
                            if first_line.startswith('Feature:'):
                                feature_name = first_line.replace('Feature:', '').strip()
                    except Exception:
                        pass  # Use filename if can't read feature name
                    
                    features.append({
                        'filename': filename,
                        'filepath': filepath,
                        'feature_name': feature_name,
                        'size_bytes': stat.st_size,
                        'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'created_time': datetime.fromtimestamp(stat.st_ctime).isoformat()
                    })
            
            # Sort by modification time (newest first)
            features.sort(key=lambda x: x['modified_time'], reverse=True)
            
            return features
            
        except Exception as e:
            logger.error(f"Error listing feature files: {e}")
            return []
    
    def validate_feature_syntax(self, feature_file: str) -> Dict[str, Any]:
        """Validate Gherkin syntax of a feature file."""
        try:
            feature_path = os.path.join(self.features_dir, feature_file)
            
            if not os.path.exists(feature_path):
                return {
                    'valid': False,
                    'error': f"Feature file not found: {feature_path}",
                    'feature_file': feature_file
                }
            
            # Use Behave's dry-run to validate syntax
            behave_cmd = [
                "behave",
                feature_path,
                "--dry-run",
                "--no-summary",
                "--format=json",
                "--outfile=/dev/null"  # We don't need the output file for validation
            ]
            
            result = subprocess.run(
                behave_cmd,
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            return {
                'valid': result.returncode == 0,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'feature_file': feature_file
            }
            
        except Exception as e:
            logger.error(f"Error validating feature syntax: {e}")
            return {
                'valid': False,
                'error': str(e),
                'feature_file': feature_file
            }
    
    def get_latest_test_results(self) -> Optional[Dict[str, Any]]:
        """Get the latest test execution results."""
        try:
            import glob
            
            # Find the latest Cucumber JSON report
            pattern = os.path.join(self.reports_dir, "cucumber_report_*.json")
            files = glob.glob(pattern)
            
            if not files:
                return None
            
            latest_file = max(files, key=os.path.getctime)
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                cucumber_data = json.load(f)
            
            # Also try to load corresponding metadata
            metadata_pattern = latest_file.replace('cucumber_report_', 'test_metadata_').replace('.json', '.json')
            metadata = None
            
            if os.path.exists(metadata_pattern):
                try:
                    with open(metadata_pattern, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                except Exception:
                    pass  # Metadata is optional
            
            return {
                'cucumber_data': cucumber_data,
                'metadata': metadata,
                'report_file': latest_file,
                'timestamp': os.path.getctime(latest_file)
            }
            
        except Exception as e:
            logger.error(f"Error getting latest test results: {e}")
            return None

# Convenience functions
def run_all_tests() -> Dict[str, Any]:
    """Quick function to run all BDD tests."""
    runner = BehaveRunner()
    return runner.run_all_features()

def run_feature(feature_file: str) -> Dict[str, Any]:
    """Quick function to run a specific feature."""
    runner = BehaveRunner()
    return runner.run_specific_feature(feature_file)

def list_features() -> List[Dict[str, Any]]:
    """Quick function to list available features."""
    runner = BehaveRunner()
    return runner.list_available_features()
