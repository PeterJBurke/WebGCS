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