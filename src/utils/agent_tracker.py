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
            'connection-testing-agent',
            'flight-controls-testing-agent',
            'navigation-testing-agent',
            'telemetry-display-testing-agent',
            'map-interface-testing-agent',
            'ui-validation-testing-agent',
            'virtual-drone-communication-agent',
            'audio-offline-testing-agent'
        ]
        
        missing_agents = [agent for agent in required_agents if agent not in self.active_agents]
        
        if missing_agents:
            print(f"❌ Missing agents: {', '.join(missing_agents)}")
            return False
        
        print("✅ All required agents registered and active")
        return True

# Global agent tracker instance
agent_tracker = AgentTracker()