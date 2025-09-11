# Initial Setup Prompt for WebGCS Project

## Send this complete prompt to Claude Code after copying all files:

---

I have set up a new WebGCS project with all required files. I've copied:

**Core Files (4):**
- CLAUDE.md (project instructions)
- WEBGCS_COMPLETE_PRD_WITH_ALL_AGENTS.md (complete PRD)
- HudLayoutExample.png (VFR HUD reference)
- HudLayoutItems.png (HUD component list)

**Agent Files (14) in .claude/agents/:**
- coordinator-agent.md
- mavlink-protocol-agent.md
- web-interface-agent.md  
- request-handlers-agent.md
- infrastructure-agent.md
- testing-agent.md
- connection-testing-agent.md
- flight-controls-testing-agent.md
- navigation-testing-agent.md
- telemetry-display-testing-agent.md
- map-interface-testing-agent.md
- ui-validation-testing-agent.md
- virtual-drone-communication-agent.md
- token-tracking-agent.md

**Environment Setup Complete:**
- UV installed and initialized
- Dependencies installed: flask flask-socketio pymavlink pytest playwright

**Please help me:**

1. **Activate all 14 agents** from the `.claude/agents/` directory
2. **Verify agent activation** by running `/agents` command
3. **Read the CLAUDE.md and PRD** to understand project requirements
4. **Initialize project structure** according to modular architecture rules
5. **Begin Phase 1 development** following the PRD specifications:
   - Implement basic MAVLink connection to virtual drone at 192.168.193.235:5678
   - Create telemetry handling with heartbeat monitoring
   - Ensure all 3 Phase 1 tests pass before proceeding

**Critical Requirements:**
- NO files over 200 lines (modular architecture)
- Use virtual drone at 192.168.193.235:5678 for testing
- Follow VFR HUD specifications exactly from reference images
- Monitor token usage across all 14 agents
- 100% test pass rate required before phase transitions
- Professional glass cockpit styling with rectangular artificial horizon

**Development Approach:**
- Test-first development (write failing test → implement → pass test)
- Use specialized agents for their designated responsibilities
- Track progress with TodoWrite tool
- Generate token usage reports every 10 tasks

The project should result in a complete, production-ready web-based ground control station with professional VFR HUD display and comprehensive drone control capabilities.

Please confirm agent activation and begin Phase 1 development according to the PRD specifications.