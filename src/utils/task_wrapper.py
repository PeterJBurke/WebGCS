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