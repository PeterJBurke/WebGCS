#!/usr/bin/env python3
"""
UI Improvement Validation Script
Validates that CSS improvements for font sizes and button spacing have been applied correctly.
"""

import re
import sys

def validate_css_improvements():
    """Validate that the CSS improvements have been applied correctly."""
    
    css_file_path = "/Users/peterburke/Documents/Code/WebGCS5/static/css/main.css"
    
    try:
        with open(css_file_path, 'r') as f:
            css_content = f.read()
    except FileNotFoundError:
        print("❌ CSS file not found!")
        return False
    
    improvements = [
        # Spacing improvements
        {
            "description": "Left column gap increased",
            "pattern": r"\.left-column\s*\{[^}]*gap:\s*0\.6rem",
            "expected": "0.6rem gap for left column"
        },
        {
            "description": "Panel padding increased",
            "pattern": r"\.panel\s*\{[^}]*padding:\s*0\.8rem",
            "expected": "0.8rem padding for panels"
        },
        {
            "description": "Connection inputs gap increased",
            "pattern": r"\.connection-inputs\s*\{[^}]*gap:\s*0\.6rem",
            "expected": "0.6rem gap for connection inputs"
        },
        {
            "description": "Connection buttons gap increased",
            "pattern": r"\.connection-buttons\s*\{[^}]*gap:\s*0\.6rem",
            "expected": "0.6rem gap for connection buttons"
        },
        {
            "description": "Button row gap increased",
            "pattern": r"\.button-row\s*\{[^}]*gap:\s*0\.6rem",
            "expected": "0.6rem gap for button rows"
        },
        {
            "description": "Navigation buttons gap increased",
            "pattern": r"\.nav-buttons\s*\{[^}]*gap:\s*0\.6rem",
            "expected": "0.6rem gap for nav buttons"
        },
        {
            "description": "Request buttons gap increased", 
            "pattern": r"\.request-buttons\s*\{[^}]*gap:\s*0\.6rem",
            "expected": "0.6rem gap for request buttons"
        },
        {
            "description": "Map controls gap increased",
            "pattern": r"\.map-controls\s*\{[^}]*gap:\s*0\.6rem",
            "expected": "0.6rem gap for map controls"
        },
        {
            "description": "Modal buttons gap increased",
            "pattern": r"\.modal-buttons\s*\{[^}]*gap:\s*0\.6rem",
            "expected": "0.6rem gap for modal buttons"
        },
        {
            "description": "Download controls gap increased",
            "pattern": r"\.download-controls\s*\{[^}]*gap:\s*0\.6rem",
            "expected": "0.6rem gap for download controls"
        },
        
        # Font size improvements
        {
            "description": "PFD panel heading font size increased",
            "pattern": r"\.pfd-panel\s+h3\s*\{[^}]*font-size:\s*1\.2rem",
            "expected": "1.2rem font size for PFD headings"
        },
        {
            "description": "Status labels font size increased",
            "pattern": r"\.status-label\s*\{[^}]*font-size:\s*14px",
            "expected": "14px font size for status labels"
        },
        {
            "description": "Status values font size increased",
            "pattern": r"\.status-value\s*\{[^}]*font-size:\s*16px",
            "expected": "16px font size for status values"
        },
        {
            "description": "Data labels font size increased",
            "pattern": r"\.data-label\s*\{[^}]*font-size:\s*13px",
            "expected": "13px font size for data labels"
        },
        {
            "description": "Data values font size increased",
            "pattern": r"\.data-value\s*\{[^}]*font-size:\s*15px",
            "expected": "15px font size for data values"
        },
        {
            "description": "Message log font size increased",
            "pattern": r"\.message-log\s*\{[^}]*font-size:\s*1\.1rem",
            "expected": "1.1rem font size for message log"
        },
        {
            "description": "Coordinates font size increased",
            "pattern": r"\.coordinates\s*\{[^}]*font-size:\s*15px",
            "expected": "15px font size for coordinates"
        },
        {
            "description": "Log entry font size increased",
            "pattern": r"\.log-entry\s*\{[^}]*font-size:\s*1\.1rem",
            "expected": "1.1rem font size for log entries"
        },
        {
            "description": "Log time font size increased",
            "pattern": r"\.log-time\s*\{[^}]*font-size:\s*1\.05rem",
            "expected": "1.05rem font size for log time"
        }
    ]
    
    validation_results = []
    
    print("🔍 Validating UI Improvements...")
    print("=" * 60)
    
    for improvement in improvements:
        # Use re.DOTALL to match across multiple lines
        if re.search(improvement["pattern"], css_content, re.DOTALL):
            validation_results.append({
                "description": improvement["description"],
                "status": "✅ PASS",
                "expected": improvement["expected"]
            })
        else:
            validation_results.append({
                "description": improvement["description"], 
                "status": "❌ FAIL",
                "expected": improvement["expected"]
            })
    
    # Print results
    passed = 0
    failed = 0
    
    for result in validation_results:
        print(f"{result['status']} {result['description']}")
        print(f"   Expected: {result['expected']}")
        if result['status'].startswith('✅'):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Validation Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All UI improvements have been successfully applied!")
        return True
    else:
        print(f"⚠️  {failed} improvements were not found in the CSS file.")
        return False

if __name__ == "__main__":
    success = validate_css_improvements()
    sys.exit(0 if success else 1)