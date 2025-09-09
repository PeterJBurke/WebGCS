# WebGCS Fresh Start - Essential Files List

## Files Required to Start a New WebGCS Project from Scratch

### 1. Main Documentation File (PRD)
**File:** `WEBGCS_COMPLETE_PRD_WITH_ALL_AGENTS.md`
- Complete Product Requirements Document with all specifications
- Contains ALL 14 specialized subagent configurations (not just 7)
- Has all 20 test specifications with Playwright MCP
- Defines modular architecture requirements
- Includes VFR HUD specifications from screenshots
- Token tracking for all agents

### 2. Environment Configuration
**File:** `.env`
```bash
DRONE_TCP_ADDRESS=192.168.193.235
DRONE_TCP_PORT=5678
WEB_SERVER_HOST=localhost
WEB_SERVER_PORT=5001
SECRET_KEY=webgcs_development_key
HEARTBEAT_TIMEOUT=30
REQUEST_STREAM_RATE_HZ=4
COMMAND_ACK_TIMEOUT=10
TELEMETRY_UPDATE_INTERVAL=0.1
```

### 3. Subagent Configuration Files
**IMPORTANT:** ALL 14 agent files must be created in `.claude/agents/` directory
**Note:** The complete configurations for all 14 agents are in `WEBGCS_COMPLETE_PRD_WITH_ALL_AGENTS.md`

The 14 required agents are:
1. `.claude/agents/coordinator-agent.md`
2. `.claude/agents/mavlink-protocol-agent.md`
3. `.claude/agents/web-interface-agent.md`
4. `.claude/agents/request-handlers-agent.md`
5. `.claude/agents/infrastructure-agent.md`
6. `.claude/agents/testing-agent.md`
7. `.claude/agents/connection-testing-agent.md`
8. `.claude/agents/flight-controls-testing-agent.md`
9. `.claude/agents/navigation-testing-agent.md`
10. `.claude/agents/telemetry-display-testing-agent.md`
11. `.claude/agents/map-interface-testing-agent.md`
12. `.claude/agents/ui-validation-testing-agent.md`
13. `.claude/agents/virtual-drone-communication-agent.md`
14. `.claude/agents/token-tracking-agent.md`

**Each agent file must have:**
- YAML frontmatter with name, description, and tools
- Specific responsibilities for their domain
- Playwright MCP tools for testing agents
- Maximum file size enforcement (200 lines)

## Setup Instructions

### Step 1: Create Project Directory
```bash
mkdir WebGCS_New
cd WebGCS_New
```

### Step 2: Copy Required Files
1. Copy `WEBGCS_COMPLETE_PRD_WITH_ALL_AGENTS.md` to project root (this is your main PRD)
2. Create `.env` file with the configuration above
3. Create `.claude/agents/` directory
4. Copy ALL 14 agent configuration files from the PRD to `.claude/agents/`
   - CRITICAL: Must have all 14 agents, not just 7
   - Each agent has specific testing responsibilities

### Step 3: Start Claude Code
```bash
# Open Claude Code in the project directory
# IMPORTANT: Restart Claude Code after creating agent files
```

### Step 4: Verify Agent Activation
Run command in Claude Code:
```
/agents
```

Should show ALL 14 agents as "active":
- coordinator-agent (active)
- mavlink-protocol-agent (active)
- web-interface-agent (active)
- request-handlers-agent (active)
- infrastructure-agent (active)
- testing-agent (active)
- connection-testing-agent (active)
- flight-controls-testing-agent (active)
- navigation-testing-agent (active)
- telemetry-display-testing-agent (active)
- map-interface-testing-agent (active)
- ui-validation-testing-agent (active)
- virtual-drone-communication-agent (active)
- token-tracking-agent (active)

**DO NOT PROCEED if any agent is not active!**

### Step 5: Start Development
Copy and paste this exact prompt into Claude Code:

```
I need to build the WebGCS drone control system following the WEBGCS_COMPLETE_PRD_WITH_ALL_AGENTS.md.

CRITICAL REQUIREMENTS:
1. First, verify ALL 14 subagents are active using /agents command
2. If any agent is not active, STOP and restart Claude Code
3. Track token usage for ALL 14 agents using token_tracker.py
4. NO files over 200 lines - break ALL files into modules
5. Use Playwright MCP to test EVERY button on the interface
6. NEVER stop until ALL 20 tests pass with 100% success rate
7. Test against real drone at 192.168.193.235:5678

The 14 required agents are:
- coordinator-agent (project management)
- mavlink-protocol-agent (drone communication)
- web-interface-agent (frontend, must break files into modules)
- request-handlers-agent (mission/fence handling)
- infrastructure-agent (deployment/logging)
- testing-agent (test coordination)
- connection-testing-agent (Playwright MCP for connect/disconnect)
- flight-controls-testing-agent (Playwright MCP for arm/disarm/takeoff)
- navigation-testing-agent (Playwright MCP for navigation)
- telemetry-display-testing-agent (Playwright MCP for PFD)
- map-interface-testing-agent (Playwright MCP for map)
- ui-validation-testing-agent (Playwright MCP for validations)
- virtual-drone-communication-agent (drone connection)
- token-tracking-agent (usage monitoring)

Start with:
1. Verify all 14 agents active with /agents
2. Set up token tracking for all agents
3. Write TEST-001 (must fail first)
4. Implement minimal code to pass TEST-001
5. Continue through all 20 tests

The website MUST be fully functional with EVERY button working:
- Connect/disconnect buttons must connect to real drone
- Arm/disarm must show confirmations and work
- Takeoff/land/RTL must send commands
- Go To navigation must work with coordinates
- Mode changes must be acknowledged
- PFD must show all 15 components from screenshots
- Map must be interactive with click-to-fly

DO NOT STOP until 100% of tests pass and website is FULLY functional.

Begin by checking /agents to confirm all 14 agents are active.
```

## File Summary

**Total files needed to start fresh:**
1. `WEBGCS_COMPLETE_PRD_WITH_ALL_AGENTS.md` - Complete PRD with all specifications
2. `.env` - Environment configuration
3. `.claude/agents/coordinator-agent.md`
4. `.claude/agents/mavlink-protocol-agent.md`
5. `.claude/agents/web-interface-agent.md`
6. `.claude/agents/request-handlers-agent.md`
7. `.claude/agents/infrastructure-agent.md`
8. `.claude/agents/testing-agent.md`
9. `.claude/agents/connection-testing-agent.md`
10. `.claude/agents/flight-controls-testing-agent.md`
11. `.claude/agents/navigation-testing-agent.md`
12. `.claude/agents/telemetry-display-testing-agent.md`
13. `.claude/agents/map-interface-testing-agent.md`
14. `.claude/agents/ui-validation-testing-agent.md`
15. `.claude/agents/virtual-drone-communication-agent.md`
16. `.claude/agents/token-tracking-agent.md`

**Total: 16 files** (1 PRD + 1 .env + 14 agent configurations)

## Important Notes

1. **MUST restart Claude Code** after creating agent files
2. **MUST verify ALL 14 agents are active** before starting (not just 7)
3. **MUST use the exact prompt** provided above that references all 14 agents
4. The AI will create everything else following the PRD
5. Development continues until ALL 20 tests pass with 100% success
6. Every button must be tested with Playwright MCP by specialized testing agents
7. Token usage is tracked for ALL 14 agents
8. **NO files over 200 lines** - web-interface-agent must break up app.py and index.html
9. Each testing agent uses Playwright MCP to test specific UI components

## Expected Outcome

After providing these files and following the setup, Claude Code will:
- Activate and coordinate ALL 14 specialized subagents
- Build a fully functional drone control website (not a mockup)
- Create modular architecture with ~50+ files (all under 200 lines)
- Implement 20 comprehensive tests using Playwright MCP
- Test EVERY button to ensure it actually controls the drone
- Connect to real drone at 192.168.193.235:5678
- Display professional VFR HUD with all 15 components
- Track token usage across ALL 14 agents with warnings at 80%
- Continue development until 100% functionality is achieved

The system will NOT stop until:
- Every button works and controls the actual drone
- All 20 tests pass with 100% success rate
- Token tracking shows usage for all agents
- VFR HUD displays correctly as shown in screenshots
- Website is FULLY FUNCTIONAL, not just a UI mockup

## Key Differences from Basic Setup

This complete setup includes:
- **14 specialized agents** instead of just 7
- **Dedicated testing agents** for each UI component using Playwright MCP
- **Enforced modular architecture** (no huge files)
- **Token tracking for all agents** with detailed reporting
- **VFR HUD specifications** from actual screenshots
- **Mandatory test-driven development** with fail-first approach
- **Real drone testing** at 192.168.193.235:5678
- **Continuous testing** until 100% pass rate