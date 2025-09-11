"""
WebGCS Logging Utility
High-performance logging system with <1ms latency requirement.
"""

import logging
import logging.handlers
import os
import time
from typing import Optional
from datetime import datetime


class HighPerformanceFormatter(logging.Formatter):
    """Custom formatter optimized for performance."""
    
    def __init__(self):
        # Pre-format the static parts to minimize runtime formatting
        super().__init__()
    
    def format(self, record):
        """High-performance log formatting with <1ms latency."""
        # Use pre-calculated timestamp for performance
        record.timestamp = time.time()
        record.iso_time = datetime.fromtimestamp(record.timestamp).isoformat()
        
        # Format: ISO_TIME | LEVEL | LOGGER | MESSAGE
        return f"{record.iso_time} | {record.levelname:8s} | {record.name:15s} | {record.getMessage()}"


class PerformanceLoggingHandler(logging.handlers.RotatingFileHandler):
    """Custom handler optimized for <1ms logging performance."""
    
    def __init__(self, filename, max_bytes=10485760, backup_count=5):
        """
        Initialize high-performance logging handler.
        
        Args:
            filename: Log file path
            max_bytes: Maximum file size before rotation (default: 10MB)
            backup_count: Number of backup files to keep
        """
        super().__init__(filename, maxBytes=max_bytes, backupCount=backup_count)
        
        # Optimize for performance
        self.setFormatter(HighPerformanceFormatter())
    
    def emit(self, record):
        """Emit log record with performance optimization."""
        try:
            # Time the logging operation to ensure <1ms requirement
            start_time = time.perf_counter()
            super().emit(record)
            end_time = time.perf_counter()
            
            # Check performance requirement (1ms = 0.001 seconds)
            latency = end_time - start_time
            if latency > 0.001:  # 1ms threshold
                print(f"WARNING: Logging latency exceeded 1ms: {latency*1000:.2f}ms")
                
        except Exception as e:
            # Fallback to prevent logging from breaking the application
            print(f"Logging error: {e}")


def setup_logger(name: str, log_file: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a high-performance logger with <1ms latency requirement.
    
    Args:
        name: Logger name
        log_file: Path to log file
        level: Logging level (default: INFO)
        
    Returns:
        Configured logger instance
    """
    # Ensure log directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # File handler for persistent logging
    file_handler = PerformanceLoggingHandler(log_file)
    file_handler.setLevel(level)
    logger.addHandler(file_handler)
    
    # Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(HighPerformanceFormatter())
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get existing logger or create new one with default settings.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    
    # If logger has no handlers, set it up with defaults
    if not logger.handlers:
        return setup_logger(name, f'logs/{name}.log')
    
    return logger


def log_performance_metric(logger: logging.Logger, operation: str, 
                         latency_ms: float, threshold_ms: float = 1.0) -> None:
    """
    Log performance metrics with threshold checking.
    
    Args:
        logger: Logger instance
        operation: Description of the operation
        latency_ms: Measured latency in milliseconds
        threshold_ms: Performance threshold in milliseconds
    """
    if latency_ms > threshold_ms:
        logger.warning(f"PERFORMANCE: {operation} exceeded {threshold_ms}ms threshold: {latency_ms:.2f}ms")
    else:
        logger.debug(f"PERFORMANCE: {operation} completed in {latency_ms:.2f}ms")


class PerformanceTimer:
    """Context manager for measuring and logging operation performance."""
    
    def __init__(self, logger: logging.Logger, operation: str, threshold_ms: float = 1.0):
        """
        Initialize performance timer.
        
        Args:
            logger: Logger instance
            operation: Description of the operation being timed
            threshold_ms: Performance threshold in milliseconds
        """
        self.logger = logger
        self.operation = operation
        self.threshold_ms = threshold_ms
        self.start_time = None
    
    def __enter__(self):
        """Start timing."""
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End timing and log results."""
        if self.start_time is not None:
            end_time = time.perf_counter()
            latency_ms = (end_time - self.start_time) * 1000
            log_performance_metric(self.logger, self.operation, latency_ms, self.threshold_ms)


# Pre-configured loggers for common use cases
webgcs_logger = None
mavlink_logger = None
performance_logger = None

def get_webgcs_logger() -> logging.Logger:
    """Get the main WebGCS logger."""
    global webgcs_logger
    if webgcs_logger is None:
        webgcs_logger = setup_logger('webgcs', 'logs/webgcs.log')
    return webgcs_logger

def get_mavlink_logger() -> logging.Logger:
    """Get the MAVLink communication logger."""
    global mavlink_logger
    if mavlink_logger is None:
        mavlink_logger = setup_logger('mavlink', 'logs/mavlink.log')
    return mavlink_logger

def get_performance_logger() -> logging.Logger:
    """Get the performance metrics logger."""
    global performance_logger
    if performance_logger is None:
        performance_logger = setup_logger('performance', 'logs/performance.log')
    return performance_logger