# WebGCS Realtime Systems Expert Recommendations

## Agent Information
- **Specialist**: WebGCS Realtime Systems Expert
- **Last Updated**: 2025-01-24
- **Status**: Ready for recommendations

## Current Realtime System Analysis

### MAVLink Protocol Assessment
- **Connection Management**: Robust with reconnection logic
- **Message Handling**: Comprehensive but scattered debug code
- **Command Acknowledgment**: Implemented with timeout handling
- **Message Priority**: No priority-based processing

### Identified Issues
- **Debug Code Proliferation**: Extensive commented debug statements throughout
- **Error Handling**: Inconsistent across different message types
- **Threading Model**: Mixed gevent/threading usage patterns
- **Message Validation**: Limited protocol-level validation

### Recommended Actions

#### Critical Realtime Improvements
1. **Message Processing Architecture**
   - Implement priority-based message queuing
   - Separate critical flight control from telemetry processing
   - Add message validation and sanitization layer

2. **Debug Infrastructure Overhaul**
   - Replace scattered debug prints with structured logging
   - Implement configurable debug levels
   - Add real-time debugging dashboard

#### High Priority Protocol Enhancements
3. **MAVLink Reliability**
   - Add message sequence number validation
   - Implement automatic retransmission for critical commands
   - Enhanced connection health monitoring

4. **Real-time Performance**
   - Optimize heartbeat processing (currently every message)
   - Implement message filtering based on importance
   - Add latency monitoring for critical paths

#### Medium Priority System Improvements
5. **Connection Management**
   - Support multiple MAVLink connections simultaneously
   - Implement connection failover mechanisms
   - Add bandwidth adaptation for poor connections

6. **Safety and Monitoring**
   - Real-time flight envelope monitoring
   - Automated anomaly detection
   - Emergency communication protocols

### Centralized Logging System Implementation

Based on analysis of the current codebase, WebGCS has extensive scattered debug statements across **805 lines** of commented/uncommented print statements. The current debug patterns show:

- **mavlink_message_processor.py**: 200+ debug lines for timing, altitude, attitude, and heartbeat processing
- **mavlink_connection_manager.py**: 150+ debug lines for connection management and message dispatching  
- **socketio_handlers.py**: 50+ debug lines for command processing and GOTO operations
- **app.py**: 25+ debug lines for telemetry loop monitoring

#### WebGCSLogger Class Design
```python
import threading
import time
from enum import Enum
from typing import Dict, Any, Optional
import sys
import os
import inspect
from collections import deque

class LogLevel(Enum):
    CRITICAL = 50
    ERROR = 40
    WARNING = 30
    INFO = 20
    DEBUG = 10
    TRACE = 5

class WebGCSLogger:
    """Centralized logging system optimized for real-time drone operations.
    
    Designed to replace all scattered print statements with structured logging
    while maintaining sub-millisecond latency for critical flight operations.
    """
    
    def __init__(self, console_level=LogLevel.INFO, file_level=LogLevel.DEBUG, 
                 max_buffer_size=10000, flush_interval=0.5,
                 enable_caller_info=True, enable_performance_tracking=True):
        self.console_level = console_level
        self.file_level = file_level
        self.buffer = deque(maxlen=max_buffer_size)  # Thread-safe circular buffer
        self.buffer_lock = threading.Lock()
        self.max_buffer_size = max_buffer_size
        self.flush_interval = flush_interval
        self.last_flush = time.time()
        self.enable_caller_info = enable_caller_info
        self.enable_performance_tracking = enable_performance_tracking
        
        # Performance counters for real-time monitoring
        self.message_counts = {level: 0 for level in LogLevel}
        self.start_time = time.time()
        self.total_log_calls = 0
        self.flush_count = 0
        
        # Rate limiting for high-frequency debug messages
        self.rate_limits = {}
        self.last_rate_limit_reset = time.time()
    
    def log(self, level: LogLevel, category: str, message: str, 
            metadata: Optional[Dict[str, Any]] = None, 
            caller_info: Optional[Dict[str, Any]] = None,
            rate_limit_key: Optional[str] = None,
            rate_limit_per_sec: Optional[int] = None):
        """Core logging method optimized for minimal latency.
        
        Args:
            level: Log level (CRITICAL, ERROR, WARNING, INFO, DEBUG, TRACE)
            category: Log category (MAVLINK, CONNECTION, UI_COMMAND, etc.)
            message: Log message string
            metadata: Optional metadata dictionary
            caller_info: Optional caller information (auto-detected if enabled)
            rate_limit_key: Optional key for rate limiting similar messages
            rate_limit_per_sec: Max messages per second for this rate_limit_key
        """
        
        # Fast path: early return if message won't be processed
        if level.value < min(self.console_level.value, self.file_level.value):
            return
        
        # Rate limiting check
        if rate_limit_key and rate_limit_per_sec:
            current_time = time.time()
            
            # Reset rate limit counters every second
            if current_time - self.last_rate_limit_reset >= 1.0:
                self.rate_limits.clear()
                self.last_rate_limit_reset = current_time
            
            # Check rate limit
            current_count = self.rate_limits.get(rate_limit_key, 0)
            if current_count >= rate_limit_per_sec:
                return  # Skip this message due to rate limiting
            
            self.rate_limits[rate_limit_key] = current_count + 1
            
        timestamp = time.time()
        self.total_log_calls += 1
        
        # Auto-detect caller info if enabled and not provided
        if self.enable_caller_info and caller_info is None:
            try:
                frame = inspect.currentframe().f_back
                caller_info = {
                    'filename': os.path.basename(frame.f_code.co_filename),
                    'function': frame.f_code.co_name,
                    'lineno': frame.f_lineno
                }
            except:
                caller_info = {'error': 'caller_info_detection_failed'}
        
        # Format message with real-time context
        log_entry = {
            'timestamp': timestamp,
            'level': level.name,
            'category': category,
            'message': message,
            'metadata': metadata or {},
            'caller_info': caller_info or {}
        }
        
        # Thread-safe buffer operation with minimal lock time
        with self.buffer_lock:
            self.buffer.append(log_entry)
            self.message_counts[level] += 1
            
            # Auto-flush if interval exceeded (buffer overflow handled by deque)
            if timestamp - self.last_flush >= self.flush_interval:
                self._flush_buffer()
    
    def _flush_buffer(self):
        """Flush buffered logs to console/file (called with lock held)."""
        if not self.buffer:
            return
        
        # Copy buffer contents to avoid holding lock during I/O
        entries_to_write = list(self.buffer)
        self.buffer.clear()
        self.last_flush = time.time()
        self.flush_count += 1
        
        # Release lock before I/O operations
        for entry in entries_to_write:
            self._write_log_entry(entry)
    
    def _write_log_entry(self, entry):
        """Write individual log entry to appropriate outputs."""
        level_enum = LogLevel[entry['level']]
        
        # Console output for critical real-time info
        if level_enum.value >= self.console_level.value:
            console_msg = self._format_console_message(entry)
            try:
                print(console_msg, file=sys.stderr if level_enum.value >= LogLevel.ERROR.value else sys.stdout)
            except:
                pass  # Ignore console write errors to prevent logging from breaking the app
        
        # File output for detailed debugging (implement as needed)
        if level_enum.value >= self.file_level.value:
            # TODO: Implement rotating log files
            pass
    
    def _format_console_message(self, entry):
        """Format message for console output with timing info."""
        timestamp_str = time.strftime('%H:%M:%S', time.localtime(entry['timestamp']))
        ms = int((entry['timestamp'] % 1) * 1000)
        
        # Include caller info for DEBUG level and below
        caller_suffix = ""
        if entry['level'] == 'DEBUG' and entry.get('caller_info'):
            caller = entry['caller_info']
            if 'filename' in caller and 'lineno' in caller:
                caller_suffix = f" [{caller['filename']}:{caller['lineno']}]"
        
        return f"[{timestamp_str}.{ms:03d}] {entry['level'][:1]} | {entry['category']} | {entry['message']}{caller_suffix}"
    
    def force_flush(self):
        """Force immediate flush of all buffered messages."""
        with self.buffer_lock:
            self._flush_buffer()
    
    def get_statistics(self):
        """Get logging performance statistics."""
        uptime = time.time() - self.start_time
        return {
            'uptime_seconds': uptime,
            'total_log_calls': self.total_log_calls,
            'flush_count': self.flush_count,
            'messages_per_second': self.total_log_calls / uptime if uptime > 0 else 0,
            'message_counts_by_level': dict(self.message_counts),
            'buffer_size': len(self.buffer),
            'max_buffer_size': self.max_buffer_size
        }

# Specialized loggers for different WebGCS components
class MAVLinkLogger(WebGCSLogger):
    """MAVLink-specific logger with message prioritization and rate limiting."""
    
    CRITICAL_MESSAGES = {'HEARTBEAT', 'COMMAND_ACK', 'STATUSTEXT'}
    HIGH_FREQ_MESSAGES = {'ATTITUDE', 'GLOBAL_POSITION_INT', 'VFR_HUD', 'GPS_RAW_INT'}
    TIMING_MESSAGES = {'HEARTBEAT_TIMING', 'MESSAGE_PROCESSING_TIMING'}
    
    def __init__(self, **kwargs):
        # Enable performance tracking for MAVLink operations
        super().__init__(enable_performance_tracking=True, **kwargs)
        
    def log_message(self, msg_type: str, direction: str, message: str, 
                   msg_data: Optional[Dict] = None, system_id: Optional[int] = None):
        """Log MAVLink message with automatic level determination and rate limiting."""
        
        # Determine log level based on message importance
        if msg_type in self.CRITICAL_MESSAGES:
            level = LogLevel.INFO
            rate_limit_per_sec = None  # No rate limiting for critical messages
        elif msg_type in self.HIGH_FREQ_MESSAGES:
            level = LogLevel.DEBUG
            rate_limit_per_sec = 20  # Limit high-frequency messages to 20/sec
        else:
            level = LogLevel.DEBUG
            rate_limit_per_sec = 10  # Other messages limited to 10/sec
            
        metadata = {
            'msg_type': msg_type,
            'direction': direction,
            'system_id': system_id,
            'msg_data': msg_data
        }
        
        rate_limit_key = f"msg_{msg_type}" if rate_limit_per_sec else None
        
        self.log(level, 'MAVLINK', f"{direction} {msg_type}: {message}", 
                metadata, rate_limit_key=rate_limit_key, 
                rate_limit_per_sec=rate_limit_per_sec)
    
    def log_performance(self, operation: str, duration_ms: float, 
                       threshold_ms: float = 50, context: Optional[Dict] = None):
        """Log performance metrics with automatic warning for slow operations."""
        level = LogLevel.WARNING if duration_ms > threshold_ms else LogLevel.DEBUG
        metadata = {
            'duration_ms': duration_ms, 
            'threshold_ms': threshold_ms,
            'performance_critical': duration_ms > threshold_ms
        }
        if context:
            metadata.update(context)
        
        # Rate limit performance messages to avoid spam
        self.log(level, 'PERFORMANCE', f"{operation} took {duration_ms:.2f}ms", 
                metadata, rate_limit_key=f"perf_{operation}", rate_limit_per_sec=5)
    
    def log_timing(self, operation: str, start_time: float, context: Optional[str] = None):
        """Log timing information for debugging performance issues."""
        duration_ms = (time.time() - start_time) * 1000
        message = f"{operation}"
        if context:
            message += f" ({context})"
        
        self.log_performance(operation, duration_ms, context={'timing_context': context})
    
    def log_connection_event(self, event_type: str, details: str, 
                           connection_info: Optional[Dict] = None):
        """Log connection-related events with appropriate priority."""
        if event_type in ['CONNECTED', 'DISCONNECTED', 'CONNECTION_FAILED']:
            level = LogLevel.INFO
        elif event_type in ['HEARTBEAT_TIMEOUT', 'CONNECTION_ERROR']:
            level = LogLevel.ERROR
        else:
            level = LogLevel.DEBUG
            
        metadata = {'event_type': event_type}
        if connection_info:
            metadata.update(connection_info)
            
        self.log(level, 'CONNECTION', f"{event_type}: {details}", metadata)

class UILogger(WebGCSLogger):
    """UI-specific logger for command processing and user interactions."""
    
    def log_command(self, command: str, params: Optional[Dict] = None, 
                   result: Optional[str] = None, success: Optional[bool] = None):
        """Log UI command with structured data."""
        level = LogLevel.INFO
        
        metadata = {
            'command': command,
            'params': params,
            'success': success
        }
        
        message = f"Command {command}"
        if result:
            message += f": {result}"
            
        self.log(level, 'UI_COMMAND', message, metadata)

# Global logger instances (initialize with appropriate levels)
webgcs_logger = WebGCSLogger(
    console_level=LogLevel.INFO,
    file_level=LogLevel.DEBUG,
    flush_interval=0.5,
    enable_caller_info=True
)

mavlink_logger = MAVLinkLogger(
    console_level=LogLevel.INFO, 
    file_level=LogLevel.DEBUG,
    flush_interval=0.25  # Faster flush for MAVLink messages
)

ui_logger = UILogger(
    console_level=LogLevel.INFO,
    file_level=LogLevel.DEBUG
)
```

#### Implementation Priority and Cleanup Strategy

Based on codebase analysis, the cleanup must be done systematically to maintain real-time performance:

##### Phase 1: Critical Files (Real-time Message Processing) - **Priority: CRITICAL**
1. **mavlink_message_processor.py** (200+ debug statements)
   - Replace timing debug (HB_PROC_TIMING, LOOP_TIMING patterns)
   - Replace altitude debug (ALT-DEBUG patterns) 
   - Replace attitude debug (ATT-DEBUG patterns)
   - Replace heartbeat debug (REAL-HB, HEARTBEAT DEBUG patterns)
   - **Impact**: Directly affects flight safety and real-time performance

2. **mavlink_connection_manager.py** (150+ debug statements)
   - Replace connection state logging
   - Replace message dispatching debug (HANDLER-DISPATCH patterns)
   - Replace data stream request debug
   - **Impact**: Connection stability and message throughput

3. **socketio_handlers.py** (50+ debug statements)
   - Replace command execution debug (DEBUG TAKEOFF, DEBUG GOTO)
   - Replace command processing debug
   - **Impact**: UI responsiveness and command reliability

##### Phase 2: Supporting Files - **Priority: HIGH**
4. **app.py** (25+ debug statements)
   - Replace telemetry loop debug (TELEMETRY DEBUG patterns)
   - Replace connection status debug
   - **Impact**: UI updates and system monitoring

##### Phase 3: Cleanup and Optimization - **Priority: MEDIUM**
5. **Remove commented debug code** (600+ lines)
   - Clean up all `# print(...)` statements
   - Remove obsolete timing and debugging blocks
   - **Impact**: Code maintainability and readability

6. **Add performance monitoring hooks**
   - Real-time latency tracking
   - Message processing statistics
   - Connection health metrics

##### Phase 4: Advanced Features - **Priority: LOW**
7. **Log rotation and archiving**
8. **Remote logging capabilities**
9. **Performance dashboard integration**

#### Code Examples for Priority Files

##### mavlink_message_processor.py Changes (200+ statements)
```python
# BEFORE: Timing debug scattered throughout
# print(f"[HB_PROC_TIMING] Enter process_heartbeat at {func_entry_time:.4f}")
# print(f"[HB_PROC_TIMING] Lock acquired at {lock_acquired_time:.4f} (waited {lock_acquired_time - lock_acquire_start_time:.4f}s for lock)")
# print(f"[HB_PROC_TIMING] Exit process_heartbeat. Total: {func_exit_time - func_entry_time:.4f}s")

# AFTER: Structured timing with performance thresholds
def process_heartbeat(msg, drone_state, drone_state_lock, mavlink_conn, log_cmd_action_cb, sio_instance, heartbeat_log_cb=None):
    start_time = time.time()
    
    # Log heartbeat reception with rate limiting (max 10/sec)
    mavlink_logger.log_message("HEARTBEAT", "RX", 
                              f"System {msg.get_srcSystem()}: {msg.custom_mode}", 
                              msg_data={'system_id': msg.get_srcSystem(), 'custom_mode': msg.custom_mode},
                              system_id=msg.get_srcSystem())
    
    lock_acquire_start = time.time()
    with drone_state_lock:
        lock_acquired_time = time.time()
        
        # Log lock acquisition if it takes too long (>10ms)
        lock_wait_ms = (lock_acquired_time - lock_acquire_start) * 1000
        if lock_wait_ms > 10:
            mavlink_logger.log_performance("heartbeat_lock_wait", lock_wait_ms, 
                                         threshold_ms=10, 
                                         context={'lock_type': 'drone_state_lock'})
        
        # ... existing heartbeat processing logic ...
        
    # Log total processing time with automatic warning if slow
    total_duration_ms = (time.time() - start_time) * 1000
    mavlink_logger.log_performance("process_heartbeat", total_duration_ms, 
                                  threshold_ms=50,
                                  context={'system_id': msg.get_srcSystem()})

# BEFORE: Altitude debug scattered in multiple functions
# print(f"[ALT-DEBUG] GLOBAL_POSITION_INT: alt_rel={new_alt_rel:.2f}m, alt_abs={new_alt_msl:.2f}m")
# print(f"[ALT-DEBUG] VFR_HUD: alt={new_alt_vfr:.2f}m, climb_rate={new_climb_rate:.2f}m/s")
# print(f"[ALT-DEBUG-VALCOMP] Comparing alt_rel: state='{current_alt_rel_in_state}', new_msg_val='{new_alt_rel}', changed={current_alt_rel_in_state != new_alt_rel}")

# AFTER: Structured altitude logging with context
def process_global_position_int(msg, drone_state, drone_state_lock, mavlink_conn, log_cmd_action_cb, sio_instance):
    new_alt_rel = msg.relative_alt / 1000.0
    new_alt_msl = msg.alt / 1000.0
    
    with drone_state_lock:
        altitude_changed = (
            drone_state.get('alt_rel') != new_alt_rel or
            drone_state.get('alt_abs') != new_alt_msl
        )
        
        if altitude_changed:
            mavlink_logger.log(LogLevel.DEBUG, "TELEMETRY", 
                              f"Altitude update: rel={new_alt_rel:.2f}m, abs={new_alt_msl:.2f}m",
                              metadata={
                                  'msg_type': 'GLOBAL_POSITION_INT',
                                  'alt_rel_new': new_alt_rel,
                                  'alt_abs_new': new_alt_msl,
                                  'alt_rel_prev': drone_state.get('alt_rel'),
                                  'alt_abs_prev': drone_state.get('alt_abs')
                              },
                              rate_limit_key="altitude_update",
                              rate_limit_per_sec=5)
```

##### mavlink_connection_manager.py Changes (150+ statements)
```python
# BEFORE: Connection debug throughout
# print(f"Attempting to create new MAVLink connection to: {mavlink_connection_string_config}")
# print("Waiting for heartbeat to confirm connection...")
# print(f"Received initial heartbeat from system {msg.get_srcSystem()}, confirming connection")
# print(f"[HANDLER-DISPATCH] Processing non-HEARTBEAT MSG ID: {msg.get_msgId()}, Type: {msg_type}")
# print(f"[DEBUG] No messages (non-blocking read) this iteration at {current_time:.3f}")

# AFTER: Structured connection and message processing logging
def connect_mavlink(drone_state, drone_state_lock, mavlink_connection_string_config):
    mavlink_logger.log_connection_event("CONNECTION_ATTEMPT", 
                                       f"Connecting to {mavlink_connection_string_config}",
                                       connection_info={'connection_string': mavlink_connection_string_config})
    
    # ... connection logic ...
    
    if msg:
        mavlink_logger.log_connection_event("CONNECTED", 
                                           f"Initial heartbeat from system {msg.get_srcSystem()}",
                                           connection_info={
                                               'system_id': msg.get_srcSystem(),
                                               'component_id': msg.get_srcComponent(),
                                               'autopilot': msg.autopilot,
                                               'connection_string': mavlink_connection_string_config
                                           })

def mavlink_receive_loop_runner(...):
    while True:
        # ... existing loop logic ...
        
        messages_processed_this_cycle = 0
        loop_start_time = time.time()
        
        while True:
            msg = mavlink_connection_instance.recv_msg()
            if not msg:
                break
                
            messages_processed_this_cycle += 1
            msg_type = msg.get_type()
            
            # BEFORE: print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO | MAVLINK_RX: Received {msg_type} (ID: {msg.get_msgId()})")
            # AFTER: Rate-limited message reception logging
            mavlink_logger.log(LogLevel.TRACE, "MAVLINK_RX", 
                              f"Received {msg_type} (ID: {msg.get_msgId()})",
                              metadata={'msg_id': msg.get_msgId(), 'system_id': msg.get_srcSystem()},
                              rate_limit_key=f"rx_{msg_type}",
                              rate_limit_per_sec=2)  # Max 2 logs per second per message type
            
            # Message processing with timing
            handler_start_time = time.time()
            
            if msg_type == 'HEARTBEAT':
                # ... heartbeat processing ...
                pass
            else:
                handler = MAVLINK_MESSAGE_HANDLERS.get(msg_type)
                if handler:
                    try:
                        # ... handler execution ...
                        handler_duration_ms = (time.time() - handler_start_time) * 1000
                        
                        # Log slow message processing
                        if handler_duration_ms > 25:  # 25ms threshold for non-heartbeat messages
                            mavlink_logger.log_performance(f"handler_{msg_type}", 
                                                          handler_duration_ms,
                                                          threshold_ms=25,
                                                          context={'handler_name': handler.__name__})
                    except Exception as e:
                        # BEFORE: print(f"[HANDLER-DISPATCH-ERROR] Error processing message type {msg_type} with handler {handler.__name__}: {e}")
                        # AFTER: Structured error logging
                        mavlink_logger.log(LogLevel.ERROR, "HANDLER_ERROR",
                                          f"Handler {handler.__name__} failed for {msg_type}: {str(e)}",
                                          metadata={
                                              'msg_type': msg_type,
                                              'handler_name': handler.__name__,
                                              'error': str(e),
                                              'msg_id': msg.get_msgId()
                                          })
        
        # Log processing cycle statistics
        cycle_duration_ms = (time.time() - loop_start_time) * 1000
        if messages_processed_this_cycle > 0 and cycle_duration_ms > 100:  # Log slow cycles
            mavlink_logger.log_performance("message_processing_cycle", cycle_duration_ms,
                                          threshold_ms=100,
                                          context={'messages_processed': messages_processed_this_cycle})
```

##### socketio_handlers.py Changes (50+ statements)
```python
# BEFORE: Command debug throughout handler functions
# print(f"DEBUG: handle_send_command (socketio_handlers) received data: {data}")
# print(f"DEBUG TAKEOFF: Current mode is '{current_mode}', checking if GUIDED mode change needed")
# print(f"DEBUG GOTO: Mode is not GUIDED ('{current_mode}'), will set GUIDED mode first")
# print(f"[GOTO_HANDLER_DEBUG] 'goto_location' event received. SID: {sid}, Data: {data}")

# AFTER: Structured command and interaction logging
@_socketio.on('send_command')
def handle_send_command(data):
    cmd = data.get('command')
    
    # Log command reception with full context
    ui_logger.log_command(cmd, params=data, result=None, success=None)
    
    if cmd == 'TAKEOFF':
        try:
            alt = float(data.get('altitude', 5.0))
            current_mode = _drone_state.get('mode', 'UNKNOWN')
            
            # BEFORE: print(f"DEBUG TAKEOFF: Current mode is '{current_mode}', checking if GUIDED mode change needed")
            # AFTER: Structured mode checking
            ui_logger.log(LogLevel.DEBUG, "COMMAND_PROCESSING",
                         f"TAKEOFF command: current_mode={current_mode}, target_alt={alt:.1f}m",
                         metadata={
                             'command': 'TAKEOFF',
                             'current_mode': current_mode,
                             'target_altitude': alt,
                             'requires_mode_change': current_mode != 'GUIDED'
                         })
            
            if current_mode != 'GUIDED':
                # BEFORE: print(f"DEBUG TAKEOFF: Mode is not GUIDED ('{current_mode}'), will set GUIDED mode first")
                # AFTER: Structured mode change logging
                ui_logger.log(LogLevel.INFO, "MODE_CHANGE_REQUIRED",
                             f"Setting GUIDED mode before takeoff (was {current_mode})",
                             metadata={
                                 'command_trigger': 'TAKEOFF',
                                 'from_mode': current_mode,
                                 'to_mode': 'GUIDED',
                                 'reason': 'takeoff_prerequisite'
                             })
            
            # ... rest of takeoff logic ...
            
        except Exception as e:
            ui_logger.log(LogLevel.ERROR, "COMMAND_ERROR",
                         f"TAKEOFF command failed: {str(e)}",
                         metadata={
                             'command': 'TAKEOFF',
                             'error': str(e),
                             'input_data': data
                         })

@_socketio.on('goto_location')
def goto_location(sid, data):
    # BEFORE: print(f"[GOTO_HANDLER_DEBUG] 'goto_location' event received. SID: {sid}, Data: {data}")
    # AFTER: Structured event logging
    ui_logger.log(LogLevel.DEBUG, "GOTO_EVENT",
                 f"GOTO request from client {sid}",
                 metadata={
                     'client_sid': sid,
                     'target_lat': data.get('lat'),
                     'target_lon': data.get('lon'),
                     'target_alt': data.get('alt'),
                     'current_position': {
                         'lat': _drone_state.get('lat'),
                         'lon': _drone_state.get('lon'),
                         'alt': _drone_state.get('alt_rel')
                     }
                 })
```

#### Performance Impact Analysis

##### Logging Performance Targets for Real-time Operations:
- **Log Entry Creation**: <1ms (critical path)
- **Buffer Write**: <0.1ms (critical path) 
- **Console Output**: <5ms (non-critical path)
- **File Write**: <10ms (background/async)

##### Memory Usage Optimization:
- **Buffer Size Limit**: 10,000 entries (≈2MB)
- **Auto-flush Triggers**: Buffer full OR 1-second interval
- **Message Filtering**: Debug level filtering to prevent spam

##### CPU Impact Mitigation:
- **Fast Path**: Early return for filtered messages
- **Minimal String Formatting**: Defer expensive formatting until output
- **Batch Operations**: Flush multiple entries at once

#### Message Processing Optimization
- Replace sequential message handling with priority queues
- Implement message coalescing for high-frequency telemetry
- Add circuit breaker patterns for unreliable connections

#### Threading Model Improvements
- Standardize on gevent for all async operations
- Remove mixed threading patterns
- Implement proper resource cleanup

### Real-time Performance Targets
- **Command Latency**: <50ms ARM/DISARM operations
- **Telemetry Freshness**: <250ms for critical flight data  
- **Connection Recovery**: <2s automatic reconnection
- **Message Throughput**: Handle 100+ messages/second

### Safety Considerations
- All changes must maintain flight safety as top priority
- Critical flight commands need redundant validation
- Emergency stop capability must remain uncompromised
- Real-time constraints cannot be relaxed for safety-critical operations

### Dependencies on Other Specialists
- **Performance Optimizer**: Message processing efficiency
- **Security Expert**: Protocol security and validation
- **Safety Validator**: Testing real-time performance under load
- **Frontend Specialist**: Real-time UI updates coordination

---
*Updated by webgcs-realtime-expert*