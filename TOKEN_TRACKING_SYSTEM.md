# Token Tracking System for WebGCS Multi-Agent Development

## Overview

This system tracks token usage across the main Claude agent and all 6 specialized subagents to optimize context management and prevent token limit issues during WebGCS development.

## Architecture

### Core Components

1. **Token Counter Module** - Estimates token usage for prompts and responses
2. **Agent Registry** - Tracks all active agents and their token usage
3. **Session Logger** - Records token usage over time with timestamps
4. **Alert System** - Warns when approaching token limits
5. **Optimization Recommendations** - Suggests ways to reduce token usage

## Implementation

### 1. Token Counter Utility

```python
# /src/utils/token_counter.py
import re
from typing import Dict, List, Tuple
from datetime import datetime, timezone
import json

class TokenCounter:
    """Estimates token usage for Claude Code multi-agent development"""
    
    # Rough approximation: 1 token ≈ 4 characters for English text
    CHARS_PER_TOKEN = 4
    
    # Claude token limits (approximate)
    CLAUDE_CONTEXT_LIMIT = 200000  # Claude Sonnet context window
    WARNING_THRESHOLD = 0.8  # Warn at 80% of limit
    
    def __init__(self):
        self.session_start = datetime.now(timezone.utc)
        self.agent_usage = {
            'main-agent': {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0},
            'mavlink-protocol-agent': {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0},
            'web-interface-agent': {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0},
            'request-handlers-agent': {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0},
            'infrastructure-agent': {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0},
            'testing-agent': {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0},
            'coordinator-agent': {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0},
        }
        self.session_log = []
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count from text content"""
        if not text:
            return 0
        
        # Remove extra whitespace
        clean_text = re.sub(r'\s+', ' ', text.strip())
        
        # Rough estimation based on character count
        char_count = len(clean_text)
        estimated_tokens = max(1, char_count // self.CHARS_PER_TOKEN)
        
        return estimated_tokens
    
    def log_agent_usage(self, agent_name: str, input_text: str, output_text: str = ''):
        """Log token usage for a specific agent"""
        input_tokens = self.estimate_tokens(input_text)
        output_tokens = self.estimate_tokens(output_text)
        total_tokens = input_tokens + output_tokens
        
        if agent_name not in self.agent_usage:
            self.agent_usage[agent_name] = {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
        
        self.agent_usage[agent_name]['input_tokens'] += input_tokens
        self.agent_usage[agent_name]['output_tokens'] += output_tokens
        self.agent_usage[agent_name]['total_tokens'] += total_tokens
        
        # Log the transaction
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'agent': agent_name,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': total_tokens,
            'cumulative_total': self.get_total_session_tokens()
        }
        self.session_log.append(log_entry)
        
        # Check for warnings
        self._check_token_limits(agent_name)
    
    def get_agent_usage(self, agent_name: str) -> Dict:
        """Get usage statistics for specific agent"""
        return self.agent_usage.get(agent_name, {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0})
    
    def get_total_session_tokens(self) -> int:
        """Get total tokens used in current session"""
        return sum(agent['total_tokens'] for agent in self.agent_usage.values())
    
    def get_usage_summary(self) -> Dict:
        """Get comprehensive usage summary"""
        total_tokens = self.get_total_session_tokens()
        session_duration = (datetime.now(timezone.utc) - self.session_start).total_seconds()
        
        return {
            'session_start': self.session_start.isoformat(),
            'session_duration_minutes': round(session_duration / 60, 2),
            'total_tokens': total_tokens,
            'tokens_per_minute': round(total_tokens / (session_duration / 60), 2) if session_duration > 0 else 0,
            'context_usage_percent': round((total_tokens / self.CLAUDE_CONTEXT_LIMIT) * 100, 2),
            'agents': self.agent_usage.copy(),
            'warnings': self._get_current_warnings()
        }
    
    def _check_token_limits(self, agent_name: str):
        """Check if approaching token limits and issue warnings"""
        total_tokens = self.get_total_session_tokens()
        usage_percent = total_tokens / self.CLAUDE_CONTEXT_LIMIT
        
        if usage_percent >= self.WARNING_THRESHOLD:
            print(f"⚠️  TOKEN WARNING: {usage_percent:.1%} of context limit used ({total_tokens:,} tokens)")
            print(f"   Triggered by: {agent_name}")
            print(f"   Recommendations: {self._get_optimization_suggestions()}")
    
    def _get_current_warnings(self) -> List[str]:
        """Get list of current token usage warnings"""
        warnings = []
        total_tokens = self.get_total_session_tokens()
        usage_percent = total_tokens / self.CLAUDE_CONTEXT_LIMIT
        
        if usage_percent >= 0.9:
            warnings.append(f"CRITICAL: {usage_percent:.1%} context usage - Consider session restart")
        elif usage_percent >= self.WARNING_THRESHOLD:
            warnings.append(f"HIGH: {usage_percent:.1%} context usage - Monitor closely")
        
        # Check individual agent usage
        for agent, usage in self.agent_usage.items():
            if usage['total_tokens'] > 20000:  # High individual usage
                warnings.append(f"Agent {agent} using high tokens: {usage['total_tokens']:,}")
        
        return warnings
    
    def _get_optimization_suggestions(self) -> List[str]:
        """Get suggestions for reducing token usage"""
        suggestions = [
            "Consider breaking large tasks into smaller chunks",
            "Use specific file paths instead of reading entire directories",
            "Restart Claude session to clear context",
            "Focus subagents on smaller, specific tasks",
            "Use Grep/Glob tools instead of reading large files"
        ]
        return suggestions
    
    def save_session_log(self, filepath: str = 'token_usage_log.json'):
        """Save session log to file"""
        log_data = {
            'session_summary': self.get_usage_summary(),
            'transaction_log': self.session_log
        }
        
        with open(filepath, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        print(f"📊 Token usage log saved to {filepath}")
    
    def print_usage_report(self):
        """Print formatted usage report to console"""
        summary = self.get_usage_summary()
        
        print("\n" + "="*60)
        print("🎯 WEBGCS TOKEN USAGE REPORT")
        print("="*60)
        print(f"Session Duration: {summary['session_duration_minutes']:.1f} minutes")
        print(f"Total Tokens: {summary['total_tokens']:,}")
        print(f"Context Usage: {summary['context_usage_percent']:.1f}%")
        print(f"Rate: {summary['tokens_per_minute']:.0f} tokens/minute")
        
        print(f"\n📊 AGENT BREAKDOWN:")
        print("-" * 40)
        for agent, usage in summary['agents'].items():
            if usage['total_tokens'] > 0:
                print(f"{agent:25}: {usage['total_tokens']:6,} tokens")
        
        if summary['warnings']:
            print(f"\n⚠️  WARNINGS:")
            for warning in summary['warnings']:
                print(f"  • {warning}")
        
        print("="*60 + "\n")

# Global token counter instance
token_counter = TokenCounter()
```

### 2. Agent Registration and Tracking

```python
# /src/utils/agent_tracker.py
from typing import Dict, List, Optional
from datetime import datetime, timezone
from .token_counter import token_counter

class AgentTracker:
    """Tracks active subagents and their task assignments"""
    
    def __init__(self):
        self.active_agents = {}
        self.agent_tasks = {}
        self.registration_time = {}
    
    def register_agent(self, agent_name: str, description: str):
        """Register a subagent as active"""
        self.active_agents[agent_name] = {
            'description': description,
            'status': 'active',
            'registered_at': datetime.now(timezone.utc).isoformat()
        }
        self.agent_tasks[agent_name] = []
        print(f"✅ Registered agent: {agent_name}")
        
        # Log the registration
        token_counter.log_agent_usage(
            agent_name=agent_name,
            input_text=f"Agent registration: {description}",
            output_text="Agent registered successfully"
        )
    
    def assign_task(self, agent_name: str, task_description: str):
        """Assign a task to a specific agent"""
        if agent_name not in self.active_agents:
            print(f"❌ Agent {agent_name} not registered")
            return False
        
        task = {
            'description': task_description,
            'assigned_at': datetime.now(timezone.utc).isoformat(),
            'status': 'assigned'
        }
        self.agent_tasks[agent_name].append(task)
        print(f"📋 Task assigned to {agent_name}: {task_description[:50]}...")
        return True
    
    def get_agent_status(self) -> Dict:
        """Get status of all registered agents"""
        return {
            'active_agents': list(self.active_agents.keys()),
            'agent_count': len(self.active_agents),
            'agents': self.active_agents.copy(),
            'tasks': {agent: len(tasks) for agent, tasks in self.agent_tasks.items()}
        }
    
    def verify_all_agents_active(self) -> bool:
        """Verify all required agents are registered and active"""
        required_agents = [
            'mavlink-protocol-agent',
            'web-interface-agent', 
            'request-handlers-agent',
            'infrastructure-agent',
            'testing-agent',
            'coordinator-agent'
        ]
        
        missing_agents = [agent for agent in required_agents if agent not in self.active_agents]
        
        if missing_agents:
            print(f"❌ Missing agents: {', '.join(missing_agents)}")
            return False
        
        print("✅ All required agents registered and active")
        return True

# Global agent tracker instance
agent_tracker = AgentTracker()
```

### 3. Integration with Task Tool Usage

```python
# /src/utils/task_wrapper.py
from .token_counter import token_counter
from .agent_tracker import agent_tracker

def track_task_usage(agent_name: str, task_prompt: str, response: str = ''):
    """Wrapper function to track token usage when using Task tool"""
    
    # Log the task assignment
    agent_tracker.assign_task(agent_name, task_prompt)
    
    # Track token usage
    token_counter.log_agent_usage(
        agent_name=agent_name,
        input_text=task_prompt,
        output_text=response
    )
    
    # Print mini-report for this task
    usage = token_counter.get_agent_usage(agent_name)
    print(f"🎯 {agent_name}: +{token_counter.estimate_tokens(task_prompt + response)} tokens "
          f"(Total: {usage['total_tokens']:,})")

def print_session_status():
    """Print current session status"""
    print("\n" + "="*50)
    print("📊 WEBGCS DEVELOPMENT SESSION STATUS")
    print("="*50)
    
    # Agent status
    agent_status = agent_tracker.get_agent_status()
    print(f"Active Agents: {agent_status['agent_count']}/6")
    
    # Token usage
    token_counter.print_usage_report()
    
    # Recommendations
    total_tokens = token_counter.get_total_session_tokens()
    if total_tokens > 50000:
        print("💡 RECOMMENDATIONS:")
        print("  • Consider saving progress and restarting session")
        print("  • Focus on smaller, specific tasks")
        print("  • Use targeted file operations")
```

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Design token tracking system architecture", "status": "completed", "activeForm": "Designing token tracking system architecture"}, {"content": "Create token tracking utility module", "status": "completed", "activeForm": "Creating token tracking utility module"}, {"content": "Add token tracking to main agent workflow", "status": "in_progress", "activeForm": "Adding token tracking to main agent workflow"}, {"content": "Add token tracking to subagent communication", "status": "pending", "activeForm": "Adding token tracking to subagent communication"}, {"content": "Update PRD with token tracking requirements", "status": "pending", "activeForm": "Updating PRD with token tracking requirements"}]