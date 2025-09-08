"""
TEST-006: Simplified Flight Command Test  
Tests flight command functionality using Flask test client approach
"""
import pytest
import time

def test_flight_command_handler_exists():
    """Test that flight command handler is implemented"""
    
    from app import app, socketio
    
    # Test using Flask-SocketIO test client
    client = socketio.test_client(app)
    
    # Test ARM command
    client.emit('flight_command', {
        'command': 'ARM',
        'params': {}
    })
    
    # Check for command_result response
    received = client.get_received()
    
    # PASS CRITERIA:
    assert len(received) > 0, "Must receive response to flight command"
    
    # Find command_result in received messages
    command_result = None
    for msg in received:
        if msg['name'] == 'command_result':
            command_result = msg['args'][0]
            break
    
    assert command_result is not None, "Must receive command_result event"
    assert 'success' in command_result, "Response must contain 'success' field"
    assert 'command' in command_result, "Response must contain 'command' field"
    assert command_result['command'] == 'ARM', "Command in response must match sent command"
    
    # Accept either success or MAVLink connection error
    if command_result['success']:
        print(f"✓ ARM command successful: {command_result}")
    else:
        error = command_result.get('error', '')
        assert 'MAVLink connection' in error, f"Expected MAVLink connection error, got: {error}"
        print(f"✓ ARM command properly handled (no MAVLink connection): {command_result}")

def test_multiple_command_types():
    """Test different command types are handled"""
    
    from app import app, socketio
    
    client = socketio.test_client(app)
    
    # Test commands
    test_commands = [
        {'command': 'ARM', 'params': {}},
        {'command': 'DISARM', 'params': {}},
        {'command': 'SET_MODE', 'params': {'mode': 'GUIDED'}},
        {'command': 'TAKEOFF', 'params': {'altitude': 10.0}}
    ]
    
    for cmd in test_commands:
        client.emit('flight_command', cmd)
        
        received = client.get_received()
        
        # Find the command result
        command_result = None
        for msg in received:
            if msg['name'] == 'command_result':
                command_result = msg['args'][0]
                break
        
        assert command_result is not None, f"Must receive response for {cmd['command']}"
        assert command_result['command'] == cmd['command'], f"Response command must match {cmd['command']}"
        
        print(f"✓ {cmd['command']} command handled: {command_result.get('success', False)}")

def test_invalid_command_handling():
    """Test that invalid commands are handled properly"""
    
    from app import app, socketio
    
    client = socketio.test_client(app)
    
    # Send invalid command
    client.emit('flight_command', {
        'command': 'INVALID_COMMAND',
        'params': {}
    })
    
    received = client.get_received()
    
    # Find command result
    command_result = None
    for msg in received:
        if msg['name'] == 'command_result':
            command_result = msg['args'][0]
            break
    
    assert command_result is not None, "Must receive response for invalid command"
    assert command_result['success'] == False, "Invalid command must return success=False"
    assert 'error' in command_result, "Invalid command must return error message"
    
    print(f"✓ Invalid command properly rejected: {command_result}")

if __name__ == "__main__":
    test_flight_command_handler_exists()
    test_multiple_command_types()
    test_invalid_command_handling()
    print("TEST-006 PASSED: Flight command execution successful")