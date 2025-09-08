"""
TEST-006: Flight Command Execution Test
Tests flight command execution through SocketIO web interface to virtual drone
"""
import pytest
import threading
import time
import socketio

def test_arm_disarm_command():
    """Test ARM/DISARM command execution through web interface"""
    
    # This will FAIL initially - no command handlers implemented (RED phase)
    try:
        from app import app, socketio as app_socketio
    except ImportError as e:
        pytest.fail(f"Cannot import app module - {e}")
    
    # Setup test client with response tracking
    command_response = {'received': False, 'result': None, 'timeout': False}
    
    try:
        # Start Flask server in background
        server_thread = threading.Thread(
            target=lambda: app_socketio.run(app, host='127.0.0.1', port=5003, debug=False, allow_unsafe_werkzeug=True),
            daemon=True
        )
        server_thread.start()
        time.sleep(2)  # Wait for server startup
        
        # Connect test client
        test_client = socketio.SimpleClient()
        test_client.connect('http://127.0.0.1:5003')
        
        print("Testing ARM command...")
        
        # Send ARM command
        test_client.emit('flight_command', {
            'command': 'ARM',
            'params': {}
        })
        
        # Wait for response
        try:
            response = test_client.receive(timeout=15)
            if response and len(response) >= 2 and response[0] == 'command_result':
                command_response['received'] = True
                command_response['result'] = response[1]
        except Exception as e:
            print(f"Error receiving response: {e}")
        
        # For this test, we accept either success OR no MAVLink connection error
        # since we're testing the command handling system, not actual drone connection
        if command_response['received']:
            # PASS CRITERIA (ALL must be true):
            assert command_response['received'], "Must receive command response"
            assert 'success' in command_response['result'], "Response must contain 'success' field"  
            assert 'command' in command_response['result'], "Response must contain 'command' field"
            assert command_response['result']['command'] == 'ARM', "Command in response must match sent command"
            
            # Accept either success or MAVLink connection error (both are valid for this test)
            if command_response['result']['success']:
                print(f"✓ ARM command successful: {command_response['result']}")
            else:
                error = command_response['result'].get('error', '')
                assert 'MAVLink connection' in error, f"Expected MAVLink connection error, got: {error}"
                print(f"✓ ARM command properly handled (no MAVLink connection): {command_response['result']}")
        else:
            pytest.fail("Command timeout - no response within 15 seconds")
        
        # Reset for DISARM test
        command_response['received'] = False
        
        print("Testing DISARM command...")
        
        # Send DISARM command
        test_client.emit('flight_command', {
            'command': 'DISARM', 
            'params': {}
        })
        
        # Wait for DISARM response
        try:
            response = test_client.receive(timeout=15)
            if response and len(response) >= 2 and response[0] == 'command_result':
                command_response['received'] = True
                command_response['result'] = response[1]
        except Exception as e:
            print(f"Error receiving DISARM response: {e}")
        
        if command_response['received']:
            assert command_response['received'], "Must receive DISARM command response"
            assert command_response['result']['command'] == 'DISARM', "DISARM command must be acknowledged"
            
            print(f"✓ DISARM command response: {command_response['result']}")
        else:
            pytest.fail("DISARM command timeout")
            
    except Exception as e:
        pytest.fail(f"ARM/DISARM command test failed: {e}")
    finally:
        try:
            test_client.disconnect()
        except:
            pass

def test_mode_change_command():
    """Test flight mode change commands"""
    
    from app import app, socketio as app_socketio
    
    test_client = socketio.SimpleClient()
    mode_response = {'received': False, 'result': None}
    mode_event = threading.Event()
    
    def mode_response_handler(data):
        mode_response['received'] = True
        mode_response['result'] = data
        mode_event.set()
    
    try:
        # Start server
        server_thread = threading.Thread(
            target=lambda: app_socketio.run(app, host='127.0.0.1', port=5004, debug=False, allow_unsafe_werkzeug=True),
            daemon=True
        )
        server_thread.start()
        time.sleep(2)
        
        # Connect and setup handler
        test_client.connect('http://127.0.0.1:5004')
        test_client.on('command_result', mode_response_handler)
        
        print("Testing GUIDED mode change...")
        
        # Send mode change command
        test_client.emit('flight_command', {
            'command': 'SET_MODE',
            'params': {'mode': 'GUIDED'}
        })
        
        # Wait for response
        if mode_event.wait(timeout=15):
            # PASS CRITERIA:
            assert mode_response['received'], "Must receive mode change response"
            assert 'success' in mode_response['result'], "Response must indicate success/failure"
            assert mode_response['result']['command'] == 'SET_MODE', "Command type must match"
            assert 'mode' in mode_response['result'], "Response must include mode information"
            
            print(f"✓ Mode change response: {mode_response['result']}")
        else:
            pytest.fail("Mode change command timeout")
            
    except Exception as e:
        pytest.fail(f"Mode change test failed: {e}")
    finally:
        try:
            test_client.disconnect()
        except:
            pass

def test_takeoff_command():
    """Test takeoff command with altitude parameter"""
    
    from app import app, socketio as app_socketio
    
    test_client = socketio.SimpleClient()
    takeoff_response = {'received': False, 'result': None}
    takeoff_event = threading.Event()
    
    def takeoff_response_handler(data):
        takeoff_response['received'] = True
        takeoff_response['result'] = data
        takeoff_event.set()
    
    try:
        # Start server
        server_thread = threading.Thread(
            target=lambda: app_socketio.run(app, host='127.0.0.1', port=5005, debug=False, allow_unsafe_werkzeug=True),
            daemon=True
        )
        server_thread.start()
        time.sleep(2)
        
        # Connect and setup handler
        test_client.connect('http://127.0.0.1:5005')
        test_client.on('command_result', takeoff_response_handler)
        
        print("Testing TAKEOFF command...")
        
        # Send takeoff command
        test_client.emit('flight_command', {
            'command': 'TAKEOFF',
            'params': {'altitude': 10.0}
        })
        
        # Wait for response
        if takeoff_event.wait(timeout=20):
            # PASS CRITERIA:
            assert takeoff_response['received'], "Must receive takeoff response"
            assert 'success' in takeoff_response['result'], "Response must indicate success/failure"
            assert takeoff_response['result']['command'] == 'TAKEOFF', "Command type must match"
            assert 'altitude' in takeoff_response['result'], "Response must include altitude"
            
            print(f"✓ Takeoff response: {takeoff_response['result']}")
        else:
            pytest.fail("Takeoff command timeout")
            
    except Exception as e:
        pytest.fail(f"Takeoff test failed: {e}")
    finally:
        try:
            test_client.disconnect()
        except:
            pass

if __name__ == "__main__":
    test_arm_disarm_command()
    test_mode_change_command() 
    test_takeoff_command()
    print("TEST-006 PASSED: Flight command execution successful")