"""
Logger integration module for WebGCS components.
Provides easy access to the high-performance logging system.

Usage:
    from src.utils.logger import get_logger
    
    logger = get_logger("mavlink")
    logger.info("Connection established")
    logger.log_telemetry(data)
"""

from .logging_system import (
    webgcs_logger,
    info,
    warning,
    error,
    critical,
    debug,
    log_telemetry
)

def get_logger(component_name: str = 'webgcs'):
    """
    Get a component-specific logger wrapper.
    
    Args:
        component_name: Name of the component (e.g., 'mavlink', 'web', 'telemetry')
    
    Returns:
        Logger wrapper with component-specific methods
    """
    class ComponentLogger:
        def __init__(self, component: str):
            self.component = component
        
        def debug(self, message: str, data: dict = None):
            debug(message, data, self.component)
        
        def info(self, message: str, data: dict = None):
            info(message, data, self.component)
        
        def warning(self, message: str, data: dict = None):
            warning(message, data, self.component)
        
        def error(self, message: str, data: dict = None):
            error(message, data, self.component)
        
        def critical(self, message: str, data: dict = None):
            critical(message, data, self.component)
        
        def log_telemetry(self, telemetry_data: dict):
            log_telemetry(telemetry_data, self.component)
        
        def get_performance_stats(self):
            return webgcs_logger.get_performance_stats()
    
    return ComponentLogger(component_name)

# Global logger for convenience
logger = get_logger()

# Export main functions for direct use
__all__ = [
    'get_logger',
    'logger',
    'info',
    'warning',
    'error',
    'critical', 
    'debug',
    'log_telemetry'
]