# Claude Settings Files in Current Session

## Global Claude Settings (~/.claude)

### Main Configuration Files
- **`/home/peter/.claude/claude.json`** - Global Claude configuration
  - Status line: npx ccusage statusline
  - disableAllHooks: false (hooks removed - using project-specific hooks instead)
  
- **`/home/peter/.claude/.credentials.json`** - Authentication credentials (sensitive)

### Plugin & Package Configuration
- **`/home/peter/.claude/plugins/config.json`** - Plugin configuration
- **`/home/peter/.claude/local/package.json`** - Local Node.js dependencies
- **`/home/peter/.claude/local/package-lock.json`** - Locked dependency versions

### Session & Runtime Files
- **Session files** (`/home/peter/.claude/sessions/*/`)
  - Multiple session directories with chat.json and stop.json files
  - Active sessions tracked with unique UUIDs
  
- **Todo files** (`/home/peter/.claude/todos/*.json`)
  - Over 100 agent todo tracking files
  - Format: `{uuid}-agent-{uuid}.json`
  
- **Log files** (`/home/peter/.claude/logs/*/`)
  - Test session logs (test, test_env_vars, sim_test, final_test, etc.)
  - Session-specific logs with UUIDs
  - Each contains stop.json and sometimes chat.json

## Project-Specific Settings (/home/peter/Documents/Code/WebGCS/.claude)

### Main Configuration
- **`.claude/claude.json`** - Project-specific configuration (detailed hooks & permissions)
  - **Hooks configured:**
    - PreToolUse: `/home/peter/Documents/Code/WebGCS/.claude/hooks/pre_tool_use.py`
    - PostToolUse: `post_tool_use.py --notify`
    - Notification: `notification.py --notify`
    - Stop: `stop.py --chat --notify`
    - SubagentStop: `subagent_stop.py --notify`
    - PreCompact: `pre_compact.py`
    - UserPromptSubmit: `user_prompt_submit.py --log-only`
    - SessionStart: `session_start.py`
  - **Status line:** Conditional ccusage check
  - **Permissions:** Extensive Bash command whitelist
  - **MCP Servers:** Browser automation (browser-mcp) on port 3000

### Local Settings Override
- **`.claude/settings.local.json`** - Permission overrides and additional directories
  - **Allowed commands:** find, cp, chmod, TTS scripts, uv run, git, python, grep, cat, pactl, curl, gh CLI, etc.
  - **Additional directories:** 
    - `/home/peter/.claude/projects/-home-peter-Documents-Code-WebGCS`
    - `/home/peter`
  - **WebSearch:** Enabled
  - **Note:** `/tmp` removed from additional directories to avoid confusion

### Agent Definitions
**`.claude/agents/*.md`** - Custom WebGCS-specific agents:
- `test-agent.md` - Simple test agent
- `webgcs-devops-expert.md` - Deployment automation & CI/CD
- `webgcs-documentation-agent.md` - Technical documentation
- `webgcs-embedded-expert.md` - Raspberry Pi & UART setup
- `webgcs-frontend-specialist.md` - Leaflet.js & offline maps
- `webgcs-performance-optimizer.md` - Real-time optimization
- `webgcs-realtime-expert.md` - MAVLink & WebSocket
- `webgcs-safety-validator.md` - Testing & safety validation
- `webgcs-security-expert.md` - Security hardening
- `webgcs-test-automation.md` - Automated browser testing

### Hook Logs
- **`.claude/hooks/logs/test/notification.json`** - Hook execution logs

## Key Configuration Details

### Global Settings (`~/.claude/claude.json`)
```json
{
  "disableAllHooks": false,
  "statusLine": ccusage integration
}
```

### Project Settings (`.claude/claude.json`)
- Comprehensive hook system for all tool lifecycle events
- Extensive Bash command permissions
- Browser automation via MCP
- All hooks use `uv run` for Python execution

### Permission System (`.claude/settings.local.json`)
- Fine-grained Bash command control
- Multi-directory access
- TTS and audio control permissions
- Web search enabled
- GitHub CLI access

## Notes
1. **Hooks Configuration**: All hooks are now managed in project-specific `.claude/claude.json` file. The global `~/.claude/claude.json` only contains statusLine and disableAllHooks settings.
2. Project settings override global settings when in project directory
3. Extensive hook system provides TTS notifications and logging (all in project config)
4. Over 100 todo tracking files indicate heavy agent usage
5. Security: Credentials isolated in `.credentials.json`
6. All project hooks use `uv` for Python environment management