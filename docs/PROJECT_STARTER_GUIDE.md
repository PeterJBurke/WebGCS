# Complete WebGCS Project Starter Kit

Here are the **essential files** you need to copy to any new Claude Code project:

## Core Documentation Files

### 1. **WEBGCS_PRD.md**
- **Purpose**: Complete product requirements and specifications  
- **Size**: Comprehensive reference document
- **Contains**: UI requirements, functional specs, test criteria, modular architecture rules
- **Usage**: Reference for "what to build" - Claude uses this for requirements validation

### 2. **IMPLEMENTATION_INSTRUCTIONS.md**
- **Purpose**: Step-by-step TDD development guide
- **Size**: Detailed execution roadmap  
- **Contains**: Phase-by-phase implementation, test specifications, setup commands
- **Usage**: Primary execution guide - Claude follows this sequentially

### 3. **REPRODUCTION_PROMPT.md** 
- **Purpose**: Technical architecture and subagent coordination
- **Size**: Architecture reference manual
- **Contains**: 6 subagent definitions, coordination protocols, code patterns
- **Usage**: Architecture guidance - Claude references for implementation decisions

### 4. **START_PROJECT_PROMPT.md**
- **Purpose**: The exact startup prompt for Claude Code
- **Size**: Copy-paste instructions
- **Contains**: Initialization sequence, subagent setup, token tracking activation
- **Usage**: **THIS IS YOUR ENTRY POINT** - copy the prompt between --- lines

### 5. **TOKEN_TRACKING_SYSTEM.md**
- **Purpose**: Token monitoring implementation and utilities
- **Size**: Complete tracking system code
- **Contains**: TokenCounter class, AgentTracker class, integration examples
- **Usage**: Reference for building token tracking (Claude implements this first)

### 6. **SUBAGENT_TOKEN_USAGE.md**
- **Purpose**: Token usage procedures during development
- **Size**: Usage instructions and procedures
- **Contains**: Monitoring procedures, warning thresholds, recovery steps
- **Usage**: Reference during development for optimal token management

## Agent Definition Files

### 7. **agents/ Directory**
- **Purpose**: Subagent definition files for Claude Code's /agent system
- **Contains**: 6 individual agent definition files:
  - `mavlink-protocol-agent.md` - MAVLink communication specialist
  - `web-interface-agent.md` - Flask-SocketIO frontend specialist  
  - `request-handlers-agent.md` - Mission/fence processing specialist
  - `infrastructure-agent.md` - Configuration/logging specialist
  - `testing-agent.md` - Test suite maintenance specialist
  - `coordinator-agent.md` - Project coordination specialist
- **Usage**: Used with `/agent` commands to create persistent subagents in Claude Code

---

## How to Use These Files

### Step 1: Project Setup
```bash
# Create new project directory
mkdir MyWebGCS
cd MyWebGCS

# Copy all essential MD files and agent definitions
cp /path/to/WEBGCS_PRD.md .
cp /path/to/IMPLEMENTATION_INSTRUCTIONS.md .
cp /path/to/REPRODUCTION_PROMPT.md .
cp /path/to/START_PROJECT_PROMPT.md .
cp /path/to/TOKEN_TRACKING_SYSTEM.md .
cp /path/to/SUBAGENT_TOKEN_USAGE.md .
cp -r /path/to/agents/ .

# Create .env file with virtual drone endpoint
cat > .env << 'EOF'
DRONE_TCP_ADDRESS=192.168.193.235
DRONE_TCP_PORT=5678
EOF
```

### Step 2: Start Development
1. Open Claude Code in the project directory
2. Open **START_PROJECT_PROMPT.md**  
3. Copy the text between the `---` lines (the actual prompt)
4. Paste into Claude Code chat

### Step 3: Agent Creation Process
You will execute this setup process to create the subagent system:

```
1. CREATE AGENT DIRECTORY STRUCTURE 📁
   mkdir -p .claude/agents

2. COPY AGENT FILES WITH CORRECT FORMAT ⚡
   Copy all agent files from agents/ to .claude/agents/
   (Files already have correct YAML frontmatter format)

3. REGISTER AGENTS IN CLAUDE CODE 🔧
   Use Claude Code interface to register agents from .claude/agents/

4. VERIFY AGENT REGISTRATION ✅
   Run: /agents
   └── Confirm all 6 agents are listed as active

5. INITIALIZE TOKEN TRACKING 📊
   └── Set up monitoring for all agents

6. IMPLEMENT WEBGCS PROJECT 🚀
   ├── Follow IMPLEMENTATION_INSTRUCTIONS.md
   ├── Use TDD (test-first development)
   ├── Reference WEBGCS_PRD.md for requirements
   └── Apply REPRODUCTION_PROMPT.md architecture
```

### Step 4: During Development
- **Token monitoring** happens automatically via SUBAGENT_TOKEN_USAGE.md
- **Progress tracking** through PROJECT_COORDINATION.md (auto-created)
- **Phase-by-phase implementation** following test-driven development
- **Automatic warnings** at 80% token usage

---

## File Dependencies Diagram

```
START_PROJECT_PROMPT.md (ENTRY POINT)
├── → IMPLEMENTATION_INSTRUCTIONS.md (execution steps)
├── → WEBGCS_PRD.md (requirements validation)
├── → REPRODUCTION_PROMPT.md (architecture decisions)
├── → TOKEN_TRACKING_SYSTEM.md (monitoring setup)
└── → SUBAGENT_TOKEN_USAGE.md (ongoing management)
```

---

## Pre-Flight Checklist

**Before starting, verify you have:**
- [ ] All 6 MD files in project directory
- [ ] .env file with `DRONE_TCP_ADDRESS=192.168.193.235`
- [ ] .env file with `DRONE_TCP_PORT=5678`
- [ ] Claude Code open in project directory

**Then:**
1. Open START_PROJECT_PROMPT.md
2. Copy the prompt between `---` lines
3. Paste into Claude Code
4. Watch the magic happen! ✨

**Result:** Complete WebGCS implementation with 6 coordinated subagents, token tracking, test-driven development, and production-ready drone control system.

---

## What You Get

**Fully Implemented:**
- Real-time MAVLink drone communication
- Web-based flight control interface
- Offline maps with tile caching
- Safety-critical command systems
- Performance-optimized logging
- Cross-platform deployment scripts
- Comprehensive test suite
- Token-optimized development process

**All automatically built using the 6-file starter kit!**