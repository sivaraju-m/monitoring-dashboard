"""
Logger utilities for monitoring dashboard
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Setup logger with consistent formatting
    
    Args:
        name: Logger name
        log_file: Optional log file path
        level: Logging level
        format_string: Custom format string
    
    Returns:
        Configured logger
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding multiple handlers
    if logger.handlers:
        return logger
    
    formatter = logging.Formatter(format_string)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

class DashboardLogger:
    """Dashboard-specific logger with context"""
    
    def __init__(self, component: str):
        self.component = component
        self.logger = setup_logger(f"dashboard.{component}")
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(f"[{self.component}] {message}", extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(f"[{self.component}] {message}", extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(f"[{self.component}] {message}", extra=kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(f"[{self.component}] {message}", extra=kwargs)
