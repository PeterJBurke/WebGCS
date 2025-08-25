#!/usr/bin/env python3
"""
Simple TTS notification script that can be called manually or via aliases.
"""
import subprocess
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

def main():
    """Play a completion notification."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get engineer name from environment
        engineer_name = os.getenv('ENGINEER_NAME', '')
        
        # Get the message from command line or use default
        if len(sys.argv) > 1:
            message = " ".join(sys.argv[1:])
        else:
            message = "Ready for next task!"
        
        # Path to TTS script (now in same directory)
        tts_script = Path(__file__).parent / "elevenlabs_tts.py"
        
        if tts_script.exists():
            # Note: elevenlabs_tts.py will append the engineer name automatically
            subprocess.run(["uv", "run", str(tts_script), message], timeout=10)
        else:
            print(f"TTS script not found at {tts_script}")
    
    except Exception as e:
        print(f"TTS notification failed: {e}")

if __name__ == "__main__":
    main()