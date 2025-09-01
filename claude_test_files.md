# Claude Test Files in WebGCS Project

## Claude-Specific Test Files

### Claude Agents
- `.claude/agents/test-agent.md` - Simple test agent for verifying Claude Code agent loading
- `.claude/agents/webgcs-test-automation.md` - Automated testing agent for WebGCS application testing

### Claude Hooks
- `.claude/hooks/test_hook.py` - Test hook script for Claude Code
- `.claude/hooks/logs/test/` - Directory containing test hook execution logs
  - `.claude/hooks/logs/test/notification.json` - Test notification configuration

## Test Documentation
- `claude_tests/test_automation_prompt.md` - Documentation for test automation procedures
- `claude_tests/test_tts_hooks.md` - Documentation for TTS (Text-to-Speech) hooks testing
- `claude_tests/test_tts.prompt` - TTS testing prompt file
- `claude_tests/claude_specific_tests.md` - Index of Claude-specific test files
- `manual_testing_guide.md` - Manual testing guide for WebGCS

## Python Test Files

### Core Application Tests
- `test_app.py` - Main application test suite
- `test_app_isolated.py` - Isolated application testing
- `simple_test.py` - Simple test cases

### MAVLink Connection Tests
- `test_mavlink_connection.py` - MAVLink connection testing
- `test_connection.py` - General connection testing
- `test_udp.py` - UDP connection testing

### Heartbeat Tests
- `test_heartbeat.py` - Heartbeat functionality testing
- `test_heartbeat_only.py` - Isolated heartbeat testing
- `test_heartbeat_timing.py` - Heartbeat timing verification

### Command Tests
- `test_arm_commands.py` - ARM/DISARM command testing
- `test_all_messages.py` - Comprehensive message testing

### Server Tests
- `test_server.py` - Server functionality testing
- `test_web_server.py` - Web server testing

## Test Directories
- `logs/test/` - Test execution logs directory
- `.claude/hooks/logs/test/` - Claude hook test logs directory

## Test Categories Summary

1. **Claude Integration Tests** (4 files)
   - Agent definitions
   - Hook scripts
   - Hook logs

2. **Documentation/Prompts** (4 files)
   - Testing guides
   - Automation prompts
   - TTS configuration

3. **Python Test Scripts** (12 files)
   - Application tests
   - Connection tests
   - Protocol tests
   - Server tests

**Total Test Files:** 20 files across various categories

## Notes
- All test files are maintained in the root directory and `.claude/` subdirectory
- Python test files focus on MAVLink protocol, connection handling, and server functionality
- Claude-specific tests include agent validation and hook execution testing
- Documentation files provide guidance for both manual and automated testing procedures