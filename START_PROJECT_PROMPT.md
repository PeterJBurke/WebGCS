# WebGCS Project Start Prompt

Use this exact prompt to start implementing the complete WebGCS project in a new Claude Code session:

---

I have a new empty project with three documentation files:
- WEBGCS_PRD.md (product requirements)  
- IMPLEMENTATION_INSTRUCTIONS.md (step-by-step guide)
- REPRODUCTION_PROMPT.md (technical architecture)

FIRST: Create all 6 specialized subagents using the /agent command:

Execute these commands one by one:
/agent mavlink-protocol-agent agents/mavlink-protocol-agent.md
/agent web-interface-agent agents/web-interface-agent.md
/agent request-handlers-agent agents/request-handlers-agent.md
/agent infrastructure-agent agents/infrastructure-agent.md
/agent testing-agent agents/testing-agent.md
/agent coordinator-agent agents/coordinator-agent.md

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

1. **Re-create subagents immediately** using these commands:
   ```
   Execute these /agent commands:
   /agent mavlink-protocol-agent agents/mavlink-protocol-agent.md
   /agent web-interface-agent agents/web-interface-agent.md
   /agent request-handlers-agent agents/request-handlers-agent.md
   /agent infrastructure-agent agents/infrastructure-agent.md
   /agent testing-agent agents/testing-agent.md
   /agent coordinator-agent agents/coordinator-agent.md
   
   Then verify all agents are active:
   /agents
   
   Only continue from where we left off in IMPLEMENTATION_INSTRUCTIONS.md once all 6 agents show as active.
   ```

2. **Check PROJECT_COORDINATION.md** for current progress and task status

3. **Resume from the last completed test phase** rather than starting over