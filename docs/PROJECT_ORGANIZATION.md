# WebGCS5 Project Organization

## Overview
This document outlines the organized folder structure for the WebGCS5 project, which was reorganized to improve maintainability and navigation.

## Folder Structure

### 📁 Core Application Files
```
./
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── main.py               # Entry point
├── pyproject.toml        # Python project configuration
├── pytest.ini           # Testing configuration
├── uv.lock              # Dependencies lock file
└── .env                 # Environment variables
```

### 📁 docs/ - Documentation
All markdown documentation files and project reports:
- `README.md` - Project overview
- `WEBGCS_PRD.md` - Product Requirements Document
- `VFR_HUD_CONFIGURATION.md` - HUD configuration guide
- `IMPLEMENTATION_INSTRUCTIONS.md` - Setup instructions
- Test reports and validation documents
- Project completion summaries

### 📁 tests/ - Testing Suite
```
tests/
├── screenshots/          # Test screenshots and visual validation
├── results/             # Test result JSON files
├── reports/             # Test report markdown files
└── test_*.py           # All test files
```

### 📁 tools/ - Utilities and Tools
```
tools/
├── mavlink/            # MAVLink protocol utilities
├── validation/         # Validation and testing utilities
├── ui/                # UI testing and screenshot tools
├── compare_timing.py   # Performance timing utilities
├── high_performance_logger.py
├── virtual_drone_simulator.py
└── demo files
```

### 📁 scripts/ - Shell Scripts
All executable shell scripts:
- `run_all_button_tests.sh`
- `run_telemetry_latency_test.sh` 
- `run_tests.sh`

### 📁 static/ - Web Assets
Frontend CSS, JavaScript, and static resources (unchanged)

### 📁 templates/ - HTML Templates
Flask Jinja2 templates (unchanged)

### 📁 src/ - Source Code
Additional source code modules (unchanged)

### 📁 agents/ - AI Agent Definitions
Specialized agent configurations (unchanged)

### 📁 logs/ - Application Logs
Runtime logs and debug information (unchanged)

## File Categories Moved

### Documentation (→ docs/)
- All `.md` files containing project documentation
- Test reports and validation summaries
- Configuration guides and instructions

### Test Files (→ tests/)
- All `test_*.py` files
- Test result JSON files (→ tests/results/)
- Screenshots and visual tests (→ tests/screenshots/)

### Utility Tools (→ tools/)
- MAVLink utilities (→ tools/mavlink/)
- Validation scripts (→ tools/validation/)  
- UI testing tools (→ tools/ui/)
- Performance and debugging utilities

### Scripts (→ scripts/)
- All executable `.sh` shell scripts
- Test runners and automation scripts

## Benefits of Organization

### 🎯 Improved Navigation
- Clear separation of concerns
- Logical grouping of related files
- Easier to find specific functionality

### 🧪 Better Testing
- All tests consolidated in one location
- Test results and reports organized
- Screenshots and visual validation separated

### 📚 Enhanced Documentation
- All documentation in central location
- Easy to maintain and update
- Clear project overview structure

### 🔧 Tool Management
- Utilities organized by category
- MAVLink tools separated
- Validation tools grouped together

## Usage Guidelines

### For Developers
- **Core app files** remain in root for easy access
- **Tests** are in `tests/` with clear subdirectories
- **Tools** are categorized by function in `tools/`
- **Documentation** is centralized in `docs/`

### For CI/CD
- Test scripts moved to `scripts/` for automation
- Test results stored in `tests/results/` 
- Clear separation between source and test files

### For Maintenance
- Documentation updates go to `docs/`
- New tools categorized appropriately
- Test artifacts organized by type

## Migration Notes

### File References Updated
Some file paths may need updating in:
- Test scripts referencing moved files
- Documentation links to moved assets
- Import statements in Python files

### Scripts Permissions
Shell scripts in `scripts/` maintain executable permissions:
```bash
chmod +x scripts/*.sh
```

### Testing Impact
- Test discovery may need path updates
- Screenshot references updated to `tests/screenshots/`
- Test result paths updated to `tests/results/`

---

**Previous Structure:** 167+ files in root directory
**Current Structure:** Organized into logical folders with clear categories

This organization makes the WebGCS5 project more maintainable, navigable, and professional while preserving all functionality and maintaining clear development workflows.