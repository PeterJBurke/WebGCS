
=== COMPLETE PFD TELEMETRY TESTING REPORT ===
Generated: 2025-09-07 12:11:49
Virtual Drone: 192.168.193.235:5678
WebGCS Server: localhost:5001

EXECUTIVE SUMMARY:
• Total Tests: 2
• Passed: 1 ✅
• Failed: 1 ❌
• Success Rate: 50.0%

TELEMETRY PERFORMANCE:
• Total Updates Collected: 1
• Telemetry Samples: 1
• Drone Connected: False
• Connection Status: disconnected

DETAILED TEST RESULTS:

✅ PASSED TEST-PFD-000: Server Health (0.00s)
   Server healthy. Status: {'drone_connected': False, 'status': 'healthy', 'timestamp': 1757272277.672532}

❌ FAILED TEST-PFD-001: Drone Connection (30.21s)
   Failed to connect to virtual drone after 30.2s timeout

PFD ELEMENTS STATUS (Latest Data):
• Attitude Indicator: ❌
• Airspeed Tape: ✅
• Altitude Tape: ✅
• Armed Status: ✅
• Flight Mode: ✅
• GPS Position: ✅

FAILED TESTS SUMMARY:
❌ TEST-PFD-001: Drone Connection: Failed to connect to virtual drone after 30.2s timeout

=== TEST REPORT COMPLETE ===
