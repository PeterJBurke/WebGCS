# Claude-Specific Test Files in WebGCS

## Claude Hook Test Files

### Test Hook Script
- **`../.claude/hooks/test_hook.py`** - Test hook script for validating Claude Code hook functionality

### Test Hook Logs
- **`../.claude/hooks/logs/test/`** - Directory containing test hook execution logs
  - `../.claude/hooks/logs/test/notification.json` - Test notification configuration and log data

## Claude Test Documentation (In This Directory)

### TTS Testing
- **`test_tts_hooks.md`** - Documentation for testing Text-to-Speech hooks integration with Claude
- **`test_tts.prompt`** - Claude prompt file for TTS testing scenarios

### Test Automation
- **`test_automation_prompt.md`** - Documentation for Claude-based test automation procedures

## Test Log Directories
- **`../.claude/hooks/logs/test/`** - Claude hook test execution logs
- **`../logs/test/`** - General test execution logs that may include Claude-related test runs

## Summary
- **Hook Test Files:** 1 Python script
- **Test Documentation:** 3 files (2 markdown, 1 prompt)
- **Test Log Locations:** 2 directories

These files are specifically designed to test and validate Claude Code's integration with the WebGCS project, focusing on:
1. Hook execution and lifecycle management
2. TTS notification system integration
3. Automated testing through Claude prompts
4. Log capture and analysis for Claude-specific operations