#!/usr/bin/env python3
"""
WebGCS Setup Verification Script
Verifies that all dependencies required for app.py are properly installed.
"""

import sys
import os
import importlib.util

def check_import(module_name, package_name=None):
    """Check if a module can be imported."""
    try:
        __import__(module_name)
        return True, None
    except ImportError as e:
        return False, str(e)

def check_file_exists(filepath):
    """Check if a file exists."""
    return os.path.isfile(filepath)

def main():
    """Main verification function."""
    print("=" * 60)
    print("WebGCS Setup Verification")
    print("=" * 60)
    
    errors = []
    warnings = []
    
    # Check Python version
    print(f"Python version: {sys.version}")
    if sys.version_info < (3, 8):
        errors.append(f"Python 3.8+ required, found {sys.version_info.major}.{sys.version_info.minor}")
    else:
        print("✓ Python version OK")
    
    # Check core dependencies from requirements.txt
    dependencies = [
        ('flask', 'Flask'),
        ('flask_socketio', 'Flask-SocketIO'),
        ('gevent', 'gevent'),
        ('gevent.websocket', 'gevent-websocket'),
        ('pymavlink', 'pymavlink'),
        ('dotenv', 'python-dotenv'),
        ('engineio', 'python-engineio'),
        ('socketio', 'python-socketio'),
    ]
    
    print("\nChecking Python dependencies:")
    for module, package in dependencies:
        success, error = check_import(module)
        if success:
            print(f"✓ {package}")
        else:
            print(f"✗ {package} - {error}")
            errors.append(f"Missing Python package: {package}")
    
    # Check specific imports used in app.py
    specific_imports = [
        'json',
        'time',
        'threading',
        'collections',
        'math',
        'traceback',
        'datetime',
        'inspect',
    ]
    
    print("\nChecking standard library modules:")
    for module in specific_imports:
        success, error = check_import(module)
        if success:
            print(f"✓ {module}")
        else:
            print(f"✗ {module} - {error}")
            errors.append(f"Missing standard library module: {module}")
    
    # Check project files
    script_dir = os.path.dirname(os.path.abspath(__file__))
    required_files = [
        'app.py',
        'config.py',
        'mavlink_connection_manager.py',
        'mavlink_message_processor.py',
        'mavlink_utils.py',
        'request_handlers.py',
        'socketio_handlers.py',
        'requirements.txt',
    ]
    
    print("\nChecking project files:")
    for filename in required_files:
        filepath = os.path.join(script_dir, filename)
        if check_file_exists(filepath):
            print(f"✓ {filename}")
        else:
            print(f"✗ {filename}")
            errors.append(f"Missing project file: {filename}")
    
    # Check template files
    template_files = [
        'templates/index.html',
        'templates/mavlink_dump.html',
    ]
    
    print("\nChecking template files:")
    for filename in template_files:
        filepath = os.path.join(script_dir, filename)
        if check_file_exists(filepath):
            print(f"✓ {filename}")
        else:
            print(f"✗ {filename}")
            warnings.append(f"Missing template file: {filename}")
    
    # Check static library files
    static_files = [
        'static/lib/leaflet.css',
        'static/lib/leaflet.js',
        'static/lib/socket.io.min.js',
        'static/lib/bootstrap.min.css',
        'static/lib/bootstrap.bundle.min.js',
    ]
    
    print("\nChecking static library files:")
    for filename in static_files:
        filepath = os.path.join(script_dir, filename)
        if check_file_exists(filepath):
            print(f"✓ {filename}")
        else:
            print(f"✗ {filename}")
            warnings.append(f"Missing static file: {filename}")
    
    # Check configuration
    env_example = os.path.join(script_dir, '.env.example')
    env_file = os.path.join(script_dir, '.env')
    
    print("\nChecking configuration:")
    if check_file_exists(env_example):
        print("✓ .env.example")
    else:
        print("✗ .env.example")
        warnings.append("Missing .env.example file")
    
    if check_file_exists(env_file):
        print("✓ .env (configuration file found)")
    else:
        print("! .env (not found - using defaults)")
        warnings.append("No .env file found, using default configuration")
    
    # Summary
    print("\n" + "=" * 60)
    if errors:
        print("❌ VERIFICATION FAILED")
        print("\nErrors that must be fixed:")
        for error in errors:
            print(f"  • {error}")
    else:
        print("✅ VERIFICATION PASSED")
    
    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  • {warning}")
    
    if not errors and not warnings:
        print("\n🎉 All checks passed! WebGCS should run properly.")
    elif not errors:
        print("\n⚠️  Setup is functional but some optional components are missing.")
    else:
        print("\n🔧 Please fix the errors above before running WebGCS.")
    
    print("=" * 60)
    return len(errors) == 0

if __name__ == "__main__":
    sys.exit(0 if main() else 1) 