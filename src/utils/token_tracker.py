"""
WebGCS Token Usage Tracking System
Monitors token consumption across all 14 specialized agents.
"""

import time
import json
import os
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class TokenUsage:
    """Token usage record for an agent."""
    agent_name: str
    input_tokens: int
    output_tokens: int
    timestamp: float
    task_description: str


class AgentTracker:
    """Tracks token usage across all WebGCS agents."""
    
    AGENTS = [
        'main', 'coordinator-agent', 'mavlink-protocol-agent',
        'web-interface-agent', 'request-handlers-agent', 'infrastructure-agent',
        'testing-agent', 'connection-testing-agent', 'flight-controls-testing-agent',
        'navigation-testing-agent', 'telemetry-display-testing-agent',
        'map-interface-testing-agent', 'ui-validation-testing-agent',
        'virtual-drone-communication-agent', 'token-tracking-agent'
    ]
    
    CONTEXT_LIMIT = 200000
    WARNING_THRESHOLD = 0.8  # 80% = 160K tokens
    CRITICAL_THRESHOLD = 0.9  # 90% = 180K tokens
    HIGH_USAGE_THRESHOLD = 20000
    
    def __init__(self, log_file: str = 'logs/token_usage.json'):
        self.log_file = log_file
        self.usage_records: List[TokenUsage] = []
        self.agent_totals: Dict[str, Dict[str, int]] = {
            agent: {'input': 0, 'output': 0, 'total': 0} for agent in self.AGENTS
        }
        self._load_existing_data()
    
    def track_usage(self, agent: str, input_tokens: int, output_tokens: int, 
                   task_description: str = "") -> None:
        if agent not in self.AGENTS:
            raise ValueError(f"Unknown agent: {agent}")
        
        usage = TokenUsage(agent, input_tokens, output_tokens, time.time(), task_description)
        self.usage_records.append(usage)
        
        self.agent_totals[agent]['input'] += input_tokens
        self.agent_totals[agent]['output'] += output_tokens
        self.agent_totals[agent]['total'] = (
            self.agent_totals[agent]['input'] + self.agent_totals[agent]['output']
        )
        
        self._save_data()
        self._check_thresholds()
    
    def get_total_usage(self) -> int:
        return sum(totals['total'] for totals in self.agent_totals.values())
    
    def get_agent_usage(self, agent: str) -> Dict[str, int]:
        if agent not in self.AGENTS:
            raise ValueError(f"Unknown agent: {agent}")
        return self.agent_totals[agent].copy()
    
    def get_high_usage_agents(self) -> List[str]:
        return [
            agent for agent, totals in self.agent_totals.items()
            if totals['total'] > self.HIGH_USAGE_THRESHOLD
        ]
    
    def get_usage_report(self) -> Dict[str, any]:
        total_usage = self.get_total_usage()
        return {
            'timestamp': datetime.now().isoformat(),
            'total_tokens': total_usage,
            'context_usage_percent': round((total_usage / self.CONTEXT_LIMIT) * 100, 2),
            'warning_threshold_reached': total_usage >= (self.CONTEXT_LIMIT * self.WARNING_THRESHOLD),
            'critical_threshold_reached': total_usage >= (self.CONTEXT_LIMIT * self.CRITICAL_THRESHOLD),
            'high_usage_agents': self.get_high_usage_agents(),
            'agent_breakdown': self.agent_totals.copy(),
            'recent_activity': [
                {
                    'agent': usage.agent_name,
                    'tokens': usage.input_tokens + usage.output_tokens,
                    'task': usage.task_description,
                    'timestamp': datetime.fromtimestamp(usage.timestamp).isoformat()
                }
                for usage in self.usage_records[-10:]
            ]
        }
    
    def _check_thresholds(self) -> None:
        total_usage = self.get_total_usage()
        usage_percent = total_usage / self.CONTEXT_LIMIT
        
        if usage_percent >= self.CRITICAL_THRESHOLD:
            print(f"CRITICAL: Token usage at {usage_percent:.1%} ({total_usage:,} tokens)")
            print("RECOMMENDATION: Start new session immediately!")
        elif usage_percent >= self.WARNING_THRESHOLD:
            print(f"WARNING: Token usage at {usage_percent:.1%} ({total_usage:,} tokens)")
            print("RECOMMENDATION: Consider optimizing tasks or preparing for session restart")
        
        high_usage = self.get_high_usage_agents()
        if high_usage:
            print(f"HIGH USAGE AGENTS: {', '.join(high_usage)}")
    
    def _load_existing_data(self) -> None:
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    data = json.load(f)
                    
                for record_data in data.get('usage_records', []):
                    usage = TokenUsage(**record_data)
                    self.usage_records.append(usage)
                
                saved_totals = data.get('agent_totals', {})
                for agent in self.AGENTS:
                    if agent in saved_totals:
                        self.agent_totals[agent] = saved_totals[agent]
                        
            except Exception as e:
                print(f"Warning: Could not load existing token data: {e}")
    
    def _save_data(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            
            data = {
                'agent_totals': self.agent_totals,
                'usage_records': [
                    {
                        'agent_name': usage.agent_name,
                        'input_tokens': usage.input_tokens,
                        'output_tokens': usage.output_tokens,
                        'timestamp': usage.timestamp,
                        'task_description': usage.task_description
                    }
                    for usage in self.usage_records
                ]
            }
            
            with open(self.log_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not save token data: {e}")


# Global tracker instance
_tracker = None

def get_tracker() -> AgentTracker:
    global _tracker
    if _tracker is None:
        _tracker = AgentTracker()
    return _tracker

def track_agent_usage(agent: str, input_tokens: int, output_tokens: int, 
                     task: str = "") -> None:
    tracker = get_tracker()
    tracker.track_usage(agent, input_tokens, output_tokens, task)