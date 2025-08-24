# WebGCS Subagent Architecture

## Overview
This document defines the new recommendation-based subagent architecture for WebGCS development. Subagents provide specialized expertise through recommendations rather than direct code implementation.

## Architecture Principles

### Core Concepts
- **Recommendation-Only**: Subagents analyze and recommend, they do not implement
- **Context-Driven**: All decisions based on shared project context
- **Collaborative**: Multiple specialists contribute to complex decisions
- **Traceable**: All recommendations documented and version-controlled

### Communication Pattern
```
1. Lead Agent → Read context.md
2. Lead Agent → Consult Specialist Subagent(s)
3. Subagent → Read context.md + domain recommendations
4. Subagent → Update domain recommendations file
5. Subagent → Update context.md with findings
6. Lead Agent → Review recommendations → Implement
7. Lead Agent → Update context.md with results
```

## File Structure

### Core Files
- `context.md` - Shared project context and current state
- `SUBAGENT_ARCHITECTURE.md` - This architecture document
- `{domain}-recommendations.md` - Individual specialist recommendation files

### Recommendation Files
Each subagent maintains a domain-specific recommendation file:

| File | Specialist | Focus Area |
|------|------------|------------|
| `devops-recommendations.md` | webgcs-devops-expert | CI/CD, deployment, infrastructure |
| `security-recommendations.md` | webgcs-security-expert | Authentication, encryption, hardening |
| `performance-recommendations.md` | webgcs-performance-optimizer | Speed, memory, real-time constraints |
| `realtime-recommendations.md` | webgcs-realtime-expert | MAVLink, WebSocket, threading |
| `frontend-recommendations.md` | webgcs-frontend-specialist | UI/UX, maps, mobile interface |
| `safety-recommendations.md` | webgcs-safety-validator | Flight safety, testing, validation |
| `embedded-recommendations.md` | webgcs-embedded-expert | Raspberry Pi, hardware, optimization |
| `documentation-recommendations.md` | webgcs-documentation-agent | Docs, guides, API reference |

## Subagent Responsibilities

### All Subagents Must
1. **Read context.md** at the start of each consultation
2. **Update their domain recommendation file** with analysis and recommendations
3. **Update context.md** with their findings and dependencies
4. **Consider interdependencies** with other specialists
5. **Prioritize recommendations** by impact and urgency
6. **Maintain recommendation history** for decision tracking

### Recommendation File Structure
Each recommendation file follows this template:

```markdown
# {Domain} Expert Recommendations

## Agent Information
- **Specialist**: {Agent Name}
- **Last Updated**: {ISO Date}
- **Status**: {Ready/Analyzing/Blocked}

## Current Assessment
{Analysis of current state in domain}

## Recommended Actions
### Critical (Immediate Action Required)
### High Priority  
### Medium Priority

## Implementation Considerations
{Technical details, dependencies, risks}

## Dependencies on Other Specialists
{Cross-domain dependencies}

---
*Updated by {agent-name}*
```

## Workflow Patterns

### Single Specialist Consultation
```
Lead Agent → context.md → Specialist Agent → Update recommendations → context.md
```

### Multi-Specialist Collaboration
```
Lead Agent → context.md → {Multiple Specialists in parallel}
Each Specialist → Read context.md + other recommendations → Update own recommendations
Lead Agent → Synthesize recommendations → Implement → Update context.md
```

### Cross-Domain Decision Making
```
1. Lead identifies cross-domain issue
2. Relevant specialists consulted simultaneously  
3. Each specialist considers others' recommendations
4. Specialists update recommendations with dependencies noted
5. Lead resolves conflicts and implements integrated solution
```

## Implementation Guidelines

### For Lead Agents
1. **Always read context.md first** to understand current project state
2. **Identify which specialists** are needed for the current task
3. **Consult specialists in logical order** (security before performance, etc.)
4. **Review all relevant recommendation files** before implementation
5. **Update context.md** with implementation results and lessons learned

### For Specialist Subagents
1. **Read context.md thoroughly** before making recommendations
2. **Review related specialist recommendations** for dependencies
3. **Provide specific, actionable recommendations** with clear priorities
4. **Include implementation complexity estimates** (Low/Medium/High)
5. **Note dependencies on other specialists** explicitly
6. **Update recommendations incrementally** as project evolves

### Recommendation Quality Standards
- **Specific**: Concrete actions, not vague suggestions
- **Prioritized**: Clear urgency and impact levels
- **Contextual**: Consider current project constraints
- **Implementable**: Technically feasible recommendations
- **Safe**: Flight safety considerations for all recommendations

## Decision Resolution

### Conflicting Recommendations
When specialists have conflicting recommendations:
1. **Document the conflict** in context.md
2. **Identify the root cause** of disagreement
3. **Consult additional specialists** if needed
4. **Lead agent makes final decision** based on project priorities
5. **Document resolution rationale** in context.md

### Priority Resolution Matrix
| Safety Impact | Performance Impact | Security Impact | Priority |
|---------------|-------------------|-----------------|----------|
| High | Any | Any | 🔥 Critical |
| Medium | High | High | 🔥 Critical |
| Low | High | Medium | ⚡ High |
| Low | Medium | Low | 📋 Medium |

## Example Workflows

### Code Quality Improvement Task
```
1. Lead Agent reads context.md
2. Consults: performance-optimizer, realtime-expert, security-expert
3. Performance Optimizer: Identifies telemetry loop inefficiencies
4. Realtime Expert: Recommends debug code cleanup
5. Security Expert: Notes input validation improvements needed
6. Lead Agent: Synthesizes recommendations, implements changes
7. Updates context.md with results
```

### New Feature Implementation
```
1. Lead Agent analyzes feature requirements
2. Consults: frontend-specialist, security-expert, safety-validator
3. Frontend Specialist: UI/UX recommendations
4. Security Expert: Authentication/authorization needs
5. Safety Validator: Safety testing requirements
6. Lead Agent: Coordinates implementation across domains
```

## Version Control and History

### Recommendation Tracking
- Each recommendation file maintains implementation history
- Context.md tracks major project milestones
- Git history provides complete decision audit trail
- Regular snapshot documentation for major releases

### Change Management
```markdown
## Change Log
- 2025-01-24: Initial architecture implementation
- [Future dates]: Major architectural changes
```

## Success Metrics

### Architecture Effectiveness
- **Decision Quality**: Fewer implementation reversals
- **Coordination Efficiency**: Reduced specialist consultation time
- **Knowledge Retention**: Context preserved across sessions
- **Implementation Success**: Higher first-attempt success rate

### Specialist Utilization
- **Coverage**: All major decisions informed by relevant specialists
- **Efficiency**: Minimal redundant consultations
- **Quality**: Specific, actionable recommendations
- **Consistency**: Uniform recommendation quality across specialists

---

This architecture ensures coordinated, expert-driven development while maintaining clear accountability and decision traceability throughout the WebGCS project lifecycle.