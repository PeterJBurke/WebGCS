#!/usr/bin/env python3
"""
Quick telemetry inspection to see what data we're receiving
"""

import time
import socketio
import json
from datetime import datetime

class TelemetryInspector:
    def __init__(self):
        self.sio = None
        self.update_count = 0
        self.samples = []
        
    def connect_and_inspect(self):
        self.sio = socketio.Client()
        
        @self.sio.event
        def connect():
            print("✅ Connected to WebGCS server")
            
        @self.sio.event
        def telemetry_update(data):
            self.update_count += 1
            if len(self.samples) < 5:  # Keep first 5 samples
                self.samples.append(data)
                
            if self.update_count % 10 == 0:
                print(f"📊 Updates: {self.update_count}")
                
        @self.sio.event
        def connection_status(data):
            print(f"🔄 Connection status: {data}")
            
        # Connect and collect data
        self.sio.connect("http://localhost:5001")
        
        # Try to connect drone
        print("🚁 Requesting drone connection...")
        self.sio.emit('connect_drone', {'ip': 'localhost', 'port': 5678})
        
        # Collect data for 10 seconds
        time.sleep(10)
        
        print(f"\n📊 Total updates received: {self.update_count}")
        print(f"📊 Sample data collected: {len(self.samples)}")
        
        for i, sample in enumerate(self.samples):
            print(f"\n--- Sample {i+1} ---")
            print(json.dumps(sample, indent=2))
            
        self.sio.disconnect()

if __name__ == "__main__":
    inspector = TelemetryInspector()
    inspector.connect_and_inspect()