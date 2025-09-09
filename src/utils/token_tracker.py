"""
Token usage tracking system for all WebGCS agents.
Monitors token consumption across 14 specialized agents plus main.
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Tuple


class AgentTracker:
    """Track token usage for all 14 agents + main."""
    
    AGENTS = [
        'main',
        'coordinator-agent',
        'mavlink-protocol-agent',
        'web-interface-agent',
        'request-handlers-agent',
        'infrastructure-agent',
        'testing-agent',
        'connection-testing-agent',
        'flight-controls-testing-agent',
        'navigation-testing-agent',
        'telemetry-display-testing-agent',
        'map-interface-testing-agent',
        'ui-validation-testing-agent',
        'virtual-drone-communication-agent',
        'token-tracking-agent'
    ]
    
    # Context limits (tokens)
    WARNING_THRESHOLD = 160_000  # 80% of 200k
    CRITICAL_THRESHOLD = 180_000  # 90% of 200k
    MAX_CONTEXT = 200_000
    
    def __init__(self, log_file: str = "token_usage.json"):
        """Initialize token tracker."""
        self.log_file = log_file
        self.usage = {agent: {'input': 0, 'output': 0, 'tasks': 0, 'total': 0} 
                     for agent in self.AGENTS}
        self.session_start = datetime.now()
        self.task_count = 0
        self.load_existing_data()
    
    def load_existing_data(self):
        """Load existing token usage data if available."""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    data = json.load(f)
                    self.usage.update(data.get('usage', {}))
                    self.task_count = data.get('task_count', 0)
            except (json.JSONDecodeError, KeyError):
                pass  # Start fresh if corrupted
    
    def record_usage(self, agent: str, input_tokens: int, output_tokens: int):
        """Record token usage for an agent."""
        if agent not in self.usage:
            self.usage[agent] = {'input': 0, 'output': 0, 'tasks': 0, 'total': 0}
        
        self.usage[agent]['input'] += input_tokens
        self.usage[agent]['output'] += output_tokens
        self.usage[agent]['tasks'] += 1
        self.usage[agent]['total'] = self.usage[agent]['input'] + self.usage[agent]['output']
        
        self.task_count += 1
        self.save_data()
        
        # Check if we need to generate report
        if self.task_count % 10 == 0:
            self.generate_report()
        
        # Check thresholds
        total_usage = self.get_total_usage()
        if total_usage > self.CRITICAL_THRESHOLD:
            self._critical_warning(total_usage)
        elif total_usage > self.WARNING_THRESHOLD:
            self._usage_warning(total_usage)
    
    def save_data(self):
        """Save token usage data to file."""
        data = {
            'usage': self.usage,
            'task_count': self.task_count,
            'session_start': self.session_start.isoformat(),
            'last_update': datetime.now().isoformat()
        }
        with open(self.log_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_total_usage(self) -> int:
        """Get total token usage across all agents."""
        return sum(agent['total'] for agent in self.usage.values())
    
    def get_agent_usage(self, agent: str) -> Dict:
        """Get usage stats for specific agent."""
        return self.usage.get(agent, {'input': 0, 'output': 0, 'tasks': 0, 'total': 0})
    
    def generate_report(self) -> str:
        """Generate comprehensive token usage report."""
        total_usage = self.get_total_usage()
        percentage = (total_usage / self.MAX_CONTEXT) * 100
        
        report = f"""
=== WebGCS Token Usage Report ===
Total Tasks: {self.task_count}
Total Tokens: {total_usage:,} / {self.MAX_CONTEXT:,} ({percentage:.1f}%)
Session Started: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}

Agent Breakdown:
"""
        
        # Sort agents by total usage (highest first)
        sorted_agents = sorted(self.usage.items(), key=lambda x: x[1]['total'], reverse=True)
        
        for agent, stats in sorted_agents:
            if stats['total'] > 0:
                agent_pct = (stats['total'] / total_usage) * 100 if total_usage > 0 else 0
                high_usage = "⚠️  HIGH" if stats['total'] > 20_000 else ""
                
                report += f"  {agent:<30} | {stats['input']:>8,} in | {stats['output']:>8,} out | {stats['total']:>8,} total | {stats['tasks']:>3} tasks | {agent_pct:>5.1f}% {high_usage}\n"
        
        if percentage > 90:
            report += "\n🚨 CRITICAL: >90% context usage! Consider agent optimization.\n"
        elif percentage > 80:
            report += "\n⚠️  WARNING: >80% context usage. Monitor closely.\n"
        
        print(report)
        return report
    
    def _usage_warning(self, total: int):
        """Issue warning for high token usage."""
        percentage = (total / self.MAX_CONTEXT) * 100
        print(f"⚠️  TOKEN USAGE WARNING: {total:,} tokens ({percentage:.1f}%) - Approaching 80% limit")
    
    def _critical_warning(self, total: int):
        """Issue critical warning for very high token usage."""
        percentage = (total / self.MAX_CONTEXT) * 100
        print(f"🚨 CRITICAL TOKEN USAGE: {total:,} tokens ({percentage:.1f}%) - Above 90% limit!")
    
    def export_stats(self, filename: str = "token_stats_export.json"):
        """Export detailed statistics for analysis."""
        export_data = {
            'summary': {
                'total_tokens': self.get_total_usage(),
                'total_tasks': self.task_count,
                'session_duration': str(datetime.now() - self.session_start),
                'agents_active': len([a for a in self.usage.values() if a['total'] > 0]),
                'percentage_used': (self.get_total_usage() / self.MAX_CONTEXT) * 100
            },
            'agents': self.usage,
            'timestamps': {
                'session_start': self.session_start.isoformat(),
                'export_time': datetime.now().isoformat()
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return export_data


# Global tracker instance
tracker = AgentTracker()


def record_agent_usage(agent: str, input_tokens: int, output_tokens: int):
    """Convenience function to record agent usage."""
    tracker.record_usage(agent, input_tokens, output_tokens)


def get_usage_report() -> str:
    """Get current usage report."""
    return tracker.generate_report()


def export_usage_stats(filename: str = None) -> Dict:
    """Export usage statistics."""
    if filename:
        return tracker.export_stats(filename)
    return tracker.export_stats()


def get_usage_summary() -> Dict:
    """Get usage summary for test runners."""
    return {
        'total_tasks': tracker.task_count,
        'total_tokens': tracker.get_total_usage(),
        'percentage_used': (tracker.get_total_usage() / tracker.MAX_CONTEXT) * 100,
        'session_start': tracker.session_start.isoformat(),
        'agents': tracker.usage
    }