"""
WebGCS High-Performance Logging Utilities
Provides easy access to the high-performance logging system for all WebGCS components
"""

from high_performance_logger import (
    HighPerformanceLogger,
    setup_logger, 
    get_logger,
    debug, info, warning, error, critical
)

# Re-export for convenience
__all__ = [
    'HighPerformanceLogger',
    'setup_logger',
    'get_logger', 
    'debug',
    'info',
    'warning', 
    'error',
    'critical'
]

# Convenience functions for WebGCS components
def log_mavlink_message(message_type, message_data, level="DEBUG"):
    """Log MAVLink message with standardized format"""
    logger = get_logger()
    logger.log(level, "MAVLink", f"{message_type}: {message_data}")

def log_web_request(method, endpoint, client_info=None, level="INFO"):
    """Log web request with standardized format"""
    logger = get_logger()
    client_str = f" from {client_info}" if client_info else ""
    logger.log(level, "WebServer", f"{method} {endpoint}{client_str}")

def log_flight_command(command, params=None, result=None, level="INFO"):
    """Log flight command with standardized format"""
    logger = get_logger()
    params_str = f" params={params}" if params else ""
    result_str = f" result={result}" if result else ""
    logger.log(level, "FlightControl", f"{command}{params_str}{result_str}")

def log_system_event(event_type, details=None, level="INFO"):
    """Log system event with standardized format"""
    logger = get_logger()
    details_str = f": {details}" if details else ""
    logger.log(level, "System", f"{event_type}{details_str}")

def log_performance_metric(metric_name, value, unit="", level="DEBUG"):
    """Log performance metric with standardized format"""
    logger = get_logger()
    unit_str = f" {unit}" if unit else ""
    logger.log(level, "Performance", f"{metric_name}={value}{unit_str}")