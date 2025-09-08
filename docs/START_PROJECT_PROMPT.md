# WebGCS Project Start Prompt

Use this exact prompt to start implementing the complete WebGCS project in a new Claude Code session:

---

I have a new empty project with three documentation files:
- WEBGCS_PRD.md (product requirements)  
- IMPLEMENTATION_INSTRUCTIONS.md (step-by-step guide)
- REPRODUCTION_PROMPT.md (technical architecture)

FIRST: Create all 6 specialized subagents:

NOTE: The agent files in agents/ directory need to be converted to proper Claude Code format first.

Execute this setup process:

1. Create .claude/agents directory:
   ```
   mkdir -p .claude/agents
   ```

2. Convert agent files to proper Claude Code format with YAML frontmatter and place them in .claude/agents/

   Required format for each agent file:
   ```markdown
   ---
   name: agent-name
   description: Brief description of agent role
   tools: Read, Write, Edit, Bash, Grep, Glob, Task
   ---
   
   Detailed system prompt defining agent's role and responsibilities...
   ```

3. After the properly formatted agents are in .claude/agents/, use the Claude Code interface to register and activate them

4. Verify registration with /agents command

SECOND: VERIFY SUBAGENT REGISTRATION - After creating all agents, verify they are active:

Run: /agents

You should see all 6 agents listed as active:
- mavlink-protocol-agent
- web-interface-agent  
- request-handlers-agent
- infrastructure-agent
- testing-agent
- coordinator-agent

IMPORTANT: If ANY agent is missing from the /agents list:
1. STOP the implementation process
2. Re-run the /agent command for the missing agent(s)
3. Run /agents again to verify all 6 are active
4. Only proceed once ALL 6 agents are confirmed active

THIRD: Set up token tracking system for the development session:
- Create the token tracking utility from TOKEN_TRACKING_SYSTEM.md
- Initialize token tracking for the main agent and all 6 subagents
- Print initial session status to establish baseline

FOURTH: Once all subagents pass the registration test and token tracking is active, implement the complete WebGCS project by following the IMPLEMENTATION_INSTRUCTIONS.md step-by-step. Use strict test-driven development - write each test first, verify it fails, then implement the minimum code to pass before moving to the next step.

IMPORTANT: Track token usage throughout development:
- Log every subagent task with input/output token counts
- Print session status every 10-15 tasks or major milestones  
- Monitor for context limit warnings (warn at 80% usage)
- Save token usage logs at major development phases

Start with Step 1 in the IMPLEMENTATION_INSTRUCTIONS.md and proceed through all phases. Use the PRD for requirements validation and the REPRODUCTION_PROMPT for architecture guidance.

The virtual drone endpoint 192.168.193.235:5678 is already configured in my .env file.

Begin with the project setup and then proceed with Phase 1: Foundation tests (TEST-001 through TEST-003).

---

## Usage Instructions

1. Copy these files to your new Claude Code project:
   - WEBGCS_PRD.md
   - IMPLEMENTATION_INSTRUCTIONS.md  
   - REPRODUCTION_PROMPT.md
   - START_PROJECT_PROMPT.md (this file)
   - TOKEN_TRACKING_SYSTEM.md
   - SUBAGENT_TOKEN_USAGE.md
   - agents/ (entire directory with all 6 agent definition files)

2. Set up your .env file with the virtual drone endpoint:
   ```
   DRONE_TCP_ADDRESS=192.168.193.235
   DRONE_TCP_PORT=5678
   ```

3. Paste the prompt above (between the --- lines) into Claude Code

4. Claude will follow the step-by-step implementation guide with test-driven development

## Handling Claude Restarts

If Claude Code needs to be restarted during development:

1. **Verify subagents are available** using:
   ```
   /agents
   ```
   
   If agents are not showing up, the .claude/agents/ directory should already contain the properly formatted agent files. Use the Claude Code interface to register them.

2. **Check PROJECT_COORDINATION.md** for current progress and task status

3. **Resume from the last completed test phase** rather than starting over

## Troubleshooting Agent Creation

If `/agents` shows no agents even after placing files in `.claude/agents/`:

1. **Verify file format**: Each agent file must have proper YAML frontmatter:
   - `name:` field matching filename (without .md extension)
   - `description:` field with brief role description
   - `tools:` field listing available tools
   - Three dashes `---` before and after YAML block

2. **Check file location**: Files must be in `.claude/agents/` not `agents/`

3. **Verify file names**: 
   - mavlink-protocol-agent.md
   - web-interface-agent.md
   - request-handlers-agent.md
   - infrastructure-agent.md
   - testing-agent.md
   - coordinator-agent.md

4. **Alternative approach**: If agent system still doesn't work, proceed with coordinated development approach using the 6 agent specialization areas as organizational principles, but without formal subagents.