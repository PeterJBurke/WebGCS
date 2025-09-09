# WebGCS Project Bootstrap Guide

## Files Required to Recreate WebGCS Project From Scratch

This document lists all files needed to bootstrap the complete WebGCS ground control station project. Copy these files manually to recreate the project.

---

## 📋 REQUIRED FILES TO COPY

### 1. Core Configuration Files

**`CLAUDE.md`**
- **Location:** Root directory
- **Purpose:** Claude Code project instructions and development guidelines
- **Critical:** Contains all development rules, agent descriptions, testing requirements

**`WEBGCS_COMPLETE_PRD_WITH_ALL_AGENTS.md`**  
- **Location:** Root directory
- **Purpose:** Complete Product Requirements Document
- **Critical:** Contains all 14 agent configurations, VFR HUD specifications, and 50+ test requirements

### 2. Reference Images

**`HudLayoutExample.png`**
- **Location:** Root directory  
- **Purpose:** Visual reference showing all 15 HUD element positions (numbered 1-15)
- **Critical:** Required for implementing professional glass cockpit VFR HUD

**`HudLayoutItems.png`**
- **Location:** Root directory
- **Purpose:** Detailed list of HUD component descriptions and functions
- **Critical:** Specifications for each of the 15 VFR HUD elements

### 3. Agent Configuration Files

**Location:** `.claude/agents/` directory

**`coordinator-agent.md`**
- Project coordination and cross-component integration specialist

**`mavlink-protocol-agent.md`**
- MAVLink communication specialist for drone protocol handling

**`web-interface-agent.md`**
- Frontend development specialist for Flask-SocketIO web application

**`request-handlers-agent.md`**
- Mission and geofence request processing specialist

**`infrastructure-agent.md`**
- System infrastructure, configuration, and deployment specialist

**`testing-agent.md`**
- Test automation and quality assurance specialist

**`connection-testing-agent.md`**
- WebGCS connection management and heartbeat testing specialist

**`flight-controls-testing-agent.md`**
- Flight control button testing and MAVLink command verification specialist

**`navigation-testing-agent.md`**
- Navigation input validation and Go To command testing specialist

**`telemetry-display-testing-agent.md`**
- Primary Flight Display and real-time telemetry testing specialist

**`map-interface-testing-agent.md`**
- Interactive map functionality and drone visualization testing specialist

**`ui-validation-testing-agent.md`**
- Input validation, error handling, and safety confirmation testing specialist

**`virtual-drone-communication-agent.md`**
- End-to-end MAVLink communication verification with virtual drone

**`token-tracking-agent.md`**
- Token usage monitoring and reporting for all agents

---

## 🚨 SETUP SEQUENCE

### 1. Copy Files
```bash
# Create new project directory
mkdir WebGCS6
cd WebGCS6

# Create .claude/agents directory  
mkdir -p .claude/agents

# Copy all 18 files listed above to appropriate locations
```

### 2. Environment Setup
```bash
# Install UV if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Initialize Python project
uv init

# Install dependencies
uv add flask flask-socketio pymavlink pytest playwright
```

### 3. AI Initialization Prompt

After copying all files, send this prompt to Claude Code:

**`INITIAL_SETUP_PROMPT.md`** (see separate file for full prompt)

**Short version:**
```
I have copied all 18 files for the WebGCS project. Please:
1. Activate all 14 agents from the .claude/agents/ directory
2. Verify all agents are active with /agents command  
3. Initialize the project structure
4. Begin Phase 1 development following the PRD specifications
```

**For the complete detailed prompt, see `INITIAL_SETUP_PROMPT.md`**

---

## 🎯 SUCCESS CRITERIA

Project is ready when:
- ✅ All 18 files copied to correct locations (4 core + 14 agents)
- ✅ All 14 agents show "active" in `/agents` command
- ✅ Environment setup completed without errors
- ✅ Ready to begin Phase 1 development

---

## 📝 FILE SUMMARY

**Total Files Required: 19**
- 4 Core files (CLAUDE.md, PRD, 2 PNG images)
- 14 Agent configuration files
- 1 Setup prompt file (INITIAL_SETUP_PROMPT.md)

**Critical Notes:**
- All files stay in project directory (no ~/.claude modifications)
- Agent files go in `.claude/agents/` within project
- VFR HUD implementation depends on reference images
- All development follows PRD specifications exactly

---

**Copy these 19 files, then send the initialization prompt to begin development.**