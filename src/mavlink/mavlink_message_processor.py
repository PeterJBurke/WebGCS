"""
MAVLink Message Processor for WebGCS
Processes and tracks MAVLink messages, especially heartbeat messages

File size: Must stay under 150 lines per WebGCS PRD
"""
import time
from typing import Dict, Optional, List
from src.utils.token_tracker import record_agent_usage


class MAVLinkMessageProcessor:
    """Processes MAVLink messages with focus on heartbeat tracking."""
    
    def __init__(self, heartbeat_timeout: float = 30.0):
        """Initialize message processor."""
        self.heartbeat_timeout = heartbeat_timeout
        self.heartbeat_count = 0
        self.heartbeat_timestamps = []
        self.last_heartbeat = None
        self.last_heartbeat_time = None
        
        # Message statistics
        self.message_counts = {}
        
        # Record token usage
        record_agent_usage('mavlink-protocol-agent', 35, 25)
    
    def process_message(self, message_data: Dict) -> bool:
        """Process incoming MAVLink message."""
        try:
            message_type = message_data.get('type', 'UNKNOWN')
            current_time = message_data.get('timestamp', time.time())
            
            # Update message statistics
            self.message_counts[message_type] = self.message_counts.get(message_type, 0) + 1
            
            # Special handling for heartbeat messages
            if message_type == 'HEARTBEAT':
                self._process_heartbeat(message_data, current_time)
            
            record_agent_usage('mavlink-protocol-agent', 20, 15)
            return True
            
        except Exception as e:
            record_agent_usage('mavlink-protocol-agent', 15, 10)
            return False
    
    def _process_heartbeat(self, heartbeat_data: Dict, timestamp: float):
        """Process heartbeat message specifically."""
        self.heartbeat_count += 1
        self.last_heartbeat = heartbeat_data
        self.last_heartbeat_time = timestamp
        
        # Keep track of heartbeat timestamps for frequency calculation
        self.heartbeat_timestamps.append(timestamp)
        
        # Only keep last 10 timestamps for frequency calculation
        if len(self.heartbeat_timestamps) > 10:
            self.heartbeat_timestamps = self.heartbeat_timestamps[-10:]
    
    def get_heartbeat_count(self) -> int:
        """Get total number of heartbeats received."""
        return self.heartbeat_count
    
    def get_last_heartbeat(self) -> Optional[Dict]:
        """Get the last heartbeat message received."""
        return self.last_heartbeat
    
    def is_heartbeat_active(self) -> bool:
        """Check if heartbeat is currently active (within timeout period)."""
        if self.last_heartbeat_time is None:
            return False
        
        current_time = time.time()
        time_since_last = current_time - self.last_heartbeat_time
        
        return time_since_last <= self.heartbeat_timeout
    
    def get_heartbeat_frequency(self) -> Optional[float]:
        """Calculate heartbeat frequency in Hz based on recent heartbeats."""
        if len(self.heartbeat_timestamps) < 2:
            return None
        
        # Calculate average time between heartbeats
        time_diffs = []
        for i in range(1, len(self.heartbeat_timestamps)):
            diff = self.heartbeat_timestamps[i] - self.heartbeat_timestamps[i-1]
            time_diffs.append(diff)
        
        if not time_diffs:
            return None
        
        average_interval = sum(time_diffs) / len(time_diffs)
        
        # Frequency = 1 / interval
        return 1.0 / average_interval if average_interval > 0 else None
    
    def get_time_since_last_heartbeat(self) -> Optional[float]:
        """Get seconds since last heartbeat."""
        if self.last_heartbeat_time is None:
            return None
        
        return time.time() - self.last_heartbeat_time
    
    def get_message_statistics(self) -> Dict[str, int]:
        """Get statistics for all message types processed."""
        return self.message_counts.copy()
    
    def reset_statistics(self):
        """Reset all message statistics."""
        self.heartbeat_count = 0
        self.heartbeat_timestamps = []
        self.last_heartbeat = None
        self.last_heartbeat_time = None
        self.message_counts = {}
        
        record_agent_usage('mavlink-protocol-agent', 15, 10)
    
    def get_processor_info(self) -> Dict:
        """Get comprehensive processor information."""
        return {
            'heartbeat_count': self.heartbeat_count,
            'heartbeat_active': self.is_heartbeat_active(),
            'heartbeat_frequency': self.get_heartbeat_frequency(),
            'time_since_last_heartbeat': self.get_time_since_last_heartbeat(),
            'message_counts': self.get_message_statistics(),
            'heartbeat_timeout': self.heartbeat_timeout
        }