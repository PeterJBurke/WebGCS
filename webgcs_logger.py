#!/usr/bin/env python3
"""
WebGCS Centralized Logging System

High-performance logging system optimized for real-time drone control operations.
Designed to replace scattered debug statements while maintaining <1ms latency for critical operations.
"""

import logging
import time
import threading
from collections import deque, defaultdict
from typing import Dict, Any, Optional, Union
import json
import sys
from datetime import datetime

class CircularBuffer:
    """High-performance circular buffer for log entries."""
    
    def __init__(self, maxsize: int = 10000):
        self.buffer = deque(maxlen=maxsize)
        self.lock = threading.Lock()
    
    def append(self, item):
        with self.lock:
            self.buffer.append(item)
    
    def get_recent(self, count: int = 100):
        with self.lock:
            return list(self.buffer)[-count:]

class WebGCSLogger:
    """
    Base logger for WebGCS with real-time performance optimization.
    Designed for <1ms log entry creation.
    """
    
    def __init__(self, module_name: str, log_level: str = "INFO"):
        self.module_name = module_name
        self.logger = logging.getLogger(f"webgcs.{module_name}")
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        
        # Performance tracking
        self.log_times = deque(maxlen=1000)  # Track last 1000 log operations
        self.performance_warning_threshold = 0.001  # 1ms
        
        # Circular buffer for recent logs
        self.recent_logs = CircularBuffer(maxsize=5000)
        
        # Setup formatter if not already configured
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s: %(message)s',
                datefmt='%H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _log_with_timing(self, level: int, message: str, **kwargs):
        """Internal logging with performance measurement."""
        start_time = time.perf_counter()
        
        # Create log entry
        log_entry = {
            'timestamp': time.time(),
            'level': logging.getLevelName(level),
            'module': self.module_name,
            'message': message,
            'kwargs': kwargs
        }
        
        # Log to standard logger
        if kwargs:
            formatted_kwargs = ', '.join(f"{k}={v}" for k, v in kwargs.items())
            full_message = f"{message} | {formatted_kwargs}"
        else:
            full_message = message
            
        self.logger.log(level, full_message)
        
        # Store in circular buffer for recent access
        self.recent_logs.append(log_entry)
        
        # Track performance
        elapsed = time.perf_counter() - start_time
        self.log_times.append(elapsed)
        
        # Warn if logging is too slow (could affect real-time performance)
        if elapsed > self.performance_warning_threshold:
            self.logger.warning(f"Slow logging operation: {elapsed*1000:.2f}ms")
    
    def debug(self, message: str, **kwargs):
        if self.logger.isEnabledFor(logging.DEBUG):
            self._log_with_timing(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        if self.logger.isEnabledFor(logging.INFO):
            self._log_with_timing(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log_with_timing(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log_with_timing(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        self._log_with_timing(logging.CRITICAL, message, **kwargs)
    
    def get_performance_stats(self):
        """Get logging performance statistics."""
        if not self.log_times:
            return {"avg_ms": 0, "max_ms": 0, "count": 0}
        
        times_ms = [t * 1000 for t in self.log_times]
        return {
            "avg_ms": sum(times_ms) / len(times_ms),
            "max_ms": max(times_ms),
            "count": len(times_ms),
            "recent_logs": len(self.recent_logs.buffer)
        }

class MAVLinkLogger(WebGCSLogger):
    """
    Specialized logger for MAVLink operations with rate limiting and message filtering.
    Optimized for high-frequency telemetry data.
    """
    
    def __init__(self, log_level: str = "INFO"):
        super().__init__("mavlink", log_level)
        
        # Rate limiting for high-frequency messages
        self.rate_limits = {
            'HEARTBEAT': 1.0,           # Max once per second
            'GLOBAL_POSITION_INT': 2.0,  # Max twice per second
            'ATTITUDE': 2.0,            # Max twice per second
            'VFR_HUD': 1.0,             # Max once per second
        }
        
        # Track last log time for each message type
        self.last_log_times = defaultdict(float)
        
        # Performance metrics for different message types
        self.message_stats = defaultdict(lambda: {'count': 0, 'total_time': 0})
    
    def debug_message(self, msg_type: str, data: Union[str, Dict[Any, Any]], **kwargs):
        """Log MAVLink messages with rate limiting and performance tracking."""
        current_time = time.time()
        
        # Apply rate limiting for high-frequency messages
        if msg_type in self.rate_limits:
            rate_limit = self.rate_limits[msg_type]
            last_time = self.last_log_times[msg_type]
            if current_time - last_time < (1.0 / rate_limit):
                return  # Skip this log due to rate limiting
            self.last_log_times[msg_type] = current_time
        
        # Format message data
        if isinstance(data, dict):
            formatted_data = ', '.join(f"{k}={v}" for k, v in data.items())
        else:
            formatted_data = str(data)
        
        message = f"MAVLink {msg_type}: {formatted_data}"
        
        # Track message-specific performance
        start_time = time.perf_counter()
        self.debug(message, msg_type=msg_type, **kwargs)
        elapsed = time.perf_counter() - start_time
        
        # Update message statistics
        stats = self.message_stats[msg_type]
        stats['count'] += 1
        stats['total_time'] += elapsed
    
    def connection_event(self, event_type: str, details: Dict[str, Any]):
        """Log connection events (connect, disconnect, error)."""
        message = f"Connection {event_type}"
        self.info(message, event=event_type, **details)
    
    def command_result(self, command: str, success: bool, result_code: Optional[int] = None, 
                      latency_ms: Optional[float] = None):
        """Log command execution results with timing."""
        level = logging.INFO if success else logging.WARNING
        status = "SUCCESS" if success else "FAILED"
        message = f"Command {command}: {status}"
        
        log_kwargs = {'command': command, 'success': success}
        if result_code is not None:
            log_kwargs['result_code'] = result_code
        if latency_ms is not None:
            log_kwargs['latency_ms'] = latency_ms
            
        self._log_with_timing(level, message, **log_kwargs)
    
    def get_message_stats(self):
        """Get per-message-type performance statistics."""
        stats = {}
        for msg_type, data in self.message_stats.items():
            if data['count'] > 0:
                avg_time_ms = (data['total_time'] / data['count']) * 1000
                stats[msg_type] = {
                    'count': data['count'],
                    'avg_time_ms': avg_time_ms,
                    'rate_limited': msg_type in self.rate_limits
                }
        return stats

class UILogger(WebGCSLogger):
    """
    Specialized logger for user interface operations and command processing.
    """
    
    def __init__(self, log_level: str = "INFO"):
        super().__init__("ui", log_level)
    
    def command_received(self, command_type: str, data: Dict[str, Any], client_id: Optional[str] = None):
        """Log incoming UI commands."""
        message = f"UI Command: {command_type}"
        log_kwargs = {'command_type': command_type, 'data': data}
        if client_id:
            log_kwargs['client_id'] = client_id
        self.info(message, **log_kwargs)
    
    def websocket_event(self, event: str, data: Any, client_count: Optional[int] = None):
        """Log WebSocket events with client information."""
        message = f"WebSocket {event}"
        log_kwargs = {'event': event}
        if client_count is not None:
            log_kwargs['client_count'] = client_count
        if data and len(str(data)) < 200:  # Avoid logging huge payloads
            log_kwargs['data'] = data
        self.debug(message, **log_kwargs)
    
    def performance_metric(self, metric_name: str, value: float, unit: str = "ms"):
        """Log performance metrics."""
        message = f"Performance: {metric_name} = {value:.2f}{unit}"
        self.info(message, metric=metric_name, value=value, unit=unit)

# Global logger instances
_logger_instances = {}
_logger_lock = threading.Lock()

def get_logger(module_name: str, logger_type: str = "base", log_level: str = "INFO") -> WebGCSLogger:
    """
    Get or create a logger instance for the specified module.
    
    Args:
        module_name: Name of the module/component
        logger_type: Type of logger ("base", "mavlink", "ui")
        log_level: Logging level
    
    Returns:
        Logger instance
    """
    key = f"{module_name}_{logger_type}"
    
    with _logger_lock:
        if key not in _logger_instances:
            if logger_type == "mavlink":
                _logger_instances[key] = MAVLinkLogger(log_level)
            elif logger_type == "ui":
                _logger_instances[key] = UILogger(log_level)
            else:
                _logger_instances[key] = WebGCSLogger(module_name, log_level)
    
    return _logger_instances[key]

def configure_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """
    Configure global logging settings for WebGCS.
    
    Args:
        log_level: Global log level
        log_file: Optional file to write logs to
    """
    # Set root logger level
    logging.getLogger("webgcs").setLevel(getattr(logging, log_level.upper()))
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            '%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        logging.getLogger("webgcs").addHandler(file_handler)

def get_all_performance_stats():
    """Get performance statistics from all active loggers."""
    stats = {}
    with _logger_lock:
        for key, logger in _logger_instances.items():
            stats[key] = logger.get_performance_stats()
            if isinstance(logger, MAVLinkLogger):
                stats[f"{key}_messages"] = logger.get_message_stats()
    return stats

# Convenience functions for common logging patterns
def log_timing(logger: WebGCSLogger, operation_name: str):
    """Context manager for timing operations."""
    class TimingContext:
        def __init__(self, logger, operation):
            self.logger = logger
            self.operation = operation
            self.start_time = None
        
        def __enter__(self):
            self.start_time = time.perf_counter()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            elapsed = time.perf_counter() - self.start_time
            elapsed_ms = elapsed * 1000
            if elapsed_ms > 100:  # Warn for operations > 100ms
                self.logger.warning(f"Slow operation: {self.operation} took {elapsed_ms:.2f}ms")
            else:
                self.logger.debug(f"Timing: {self.operation} took {elapsed_ms:.2f}ms")
    
    return TimingContext(logger, operation_name)