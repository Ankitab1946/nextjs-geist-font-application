"""Utility functions for the BDD Demo project."""

import os
import json
import logging
import subprocess
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Set up logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('bdd-demo.log')
        ]
    )
    return logging.getLogger(__name__)

def ensure_directory_exists(directory: str) -> None:
    """Ensure a directory exists, create if it doesn't."""
    Path(directory).mkdir(parents=True, exist_ok=True)

def save_json_file(data: Dict[Any, Any], filepath: str) -> bool:
    """Save data as JSON file."""
    try:
        ensure_directory_exists(os.path.dirname(filepath))
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logging.error(f"Error saving JSON file {filepath}: {e}")
        return False

def load_json_file(filepath: str) -> Optional[Dict[Any, Any]]:
    """Load data from JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading JSON file {filepath}: {e}")
        return None

def save_text_file(content: str, filepath: str) -> bool:
    """Save text content to file."""
    try:
        ensure_directory_exists(os.path.dirname(filepath))
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        logging.error(f"Error saving text file {filepath}: {e}")
        return False

def load_text_file(filepath: str) -> Optional[str]:
    """Load text content from file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logging.error(f"Error loading text file {filepath}: {e}")
        return None

def get_timestamp() -> str:
    """Get current timestamp as string."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def get_commit_hash() -> Optional[str]:
    """Get current git commit hash if available."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def format_test_duration(start_time: datetime, end_time: datetime) -> str:
    """Format test duration in human-readable format."""
    duration = end_time - start_time
    total_seconds = int(duration.total_seconds())
    minutes, seconds = divmod(total_seconds, 60)
    
    if minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()

def get_file_size_mb(filepath: str) -> float:
    """Get file size in MB."""
    try:
        size_bytes = os.path.getsize(filepath)
        return round(size_bytes / (1024 * 1024), 2)
    except OSError:
        return 0.0

class TestMetadata:
    """Class to handle test execution metadata."""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.end_time = None
        self.commit_hash = get_commit_hash()
        self.test_results = {}
        
    def mark_complete(self):
        """Mark test execution as complete."""
        self.end_time = datetime.now()
        
    def get_duration(self) -> str:
        """Get formatted test duration."""
        if self.end_time:
            return format_test_duration(self.start_time, self.end_time)
        return "In progress..."
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.get_duration(),
            'commit_hash': self.commit_hash,
            'test_results': self.test_results
        }
