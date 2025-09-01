# TTS Hook Test Prompts

## Test 1: Automated TTS Hook Verification
Test if the stop hook is being called and TTS is working:
```
1. Check if the stop hook is being triggered by looking at the latest log files in ~/.claude/logs/
2. Run the stop hook manually with test data and verify audio plays
3. Test the TTS script directly and confirm you hear audio
4. Report whether each step succeeded or failed
```

## Test 2: Multi-step Task with Todo List
Create a todo list and complete multiple tasks to test TTS at completion:
```
Create a todo list with these tasks:
1. Check Python version
2. List files in current directory
3. Show current date and time
Then complete all tasks.
```

## Test 3: Code Task
Write a simple Python function that adds two numbers and test it:
```
Write a Python function called add_numbers that takes two parameters and returns their sum. Save it to test_add.py and run it with arguments 5 and 3.
```

## Test 4: Direct TTS Test
Test the TTS functionality directly:
```
test tts functionality
```

## Test 5: Complex Task with Completion
Analyze the WebGCS codebase and provide a summary of the main components:
```
List the 5 most important Python files in the WebGCS project and briefly describe what each does.
```

## Manual Hook Test Commands

### Test stop hook directly:
```bash
echo '{"session_id": "test", "stop_hook_active": true}' | uv run /home/peter/.claude/hooks/stop
```

### Test TTS script directly:
```bash
uv run /home/peter/.claude/hooks/utils/tts/elevenlabs_tts.py "Testing TTS directly"
```

### Test WebGCS TTS:
```bash
uv run tts/elevenlabs_tts.py "Testing WebGCS TTS"
```

## Environment Check
```bash
# Check if environment variables are set
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('ELEVENLABS_API_KEY:', 'Set' if os.getenv('ELEVENLABS_API_KEY') else 'Not set'); print('ENGINEER_NAME:', os.getenv('ENGINEER_NAME', 'Not set'))"
```

## Notes
- The stop hook should trigger TTS at the end of each Claude response
- TTS will say the completion message followed by the engineer name (e.g., "Task complete, Peter")
- If TTS doesn't play, check:
  1. ELEVENLABS_API_KEY is set in .env
  2. Audio output device is working
  3. Hook permissions are executable
  4. No errors in ~/.claude/logs/*/stop.json