"""Agent module for NBX compliance checking using LiteLLM and MCP."""

import os
from typing import Dict, Any, Optional
from agents import Agent, Runner
from agents.extensions.models.litellm_model import LitellmModel
from .mcp import create_mcp_server
from .prompts import SYSTEM_INSTRUCTIONS


async def run_once(
    rule: str,
    scope: Dict[str, str],
    model: str,
    api_key: Optional[str],
    mcp_dir: str,
    netbox_url: str,
    netbox_token: str,
    limit: Optional[int] = None,
    max_steps: int = 25,
) -> Dict[str, Any]:
    """
    Run a single compliance check against NetBox.
    
    Args:
        rule: Natural language compliance rule
        scope: Scope dictionary (site, rack, device)
        model: Model identifier for LiteLLM
        api_key: API key for the model provider
        mcp_dir: Directory containing the NetBox MCP server
        netbox_url: NetBox instance URL
        netbox_token: NetBox API token
        limit: Optional limit on number of objects to check
        max_steps: Maximum number of agent steps
    
    Returns:
        Dictionary containing compliance check results
    """
    
    # Create MCP server connection
    async with create_mcp_server(
        mcp_dir=mcp_dir,
        netbox_url=netbox_url,
        netbox_token=netbox_token,
    ) as server:
        
        # Set OPENAI_API_KEY to suppress trace warnings (use actual key if available)
        if api_key and not os.getenv("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = api_key
        elif not os.getenv("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = os.getenv("API_KEY", "dummy")
        
        # Initialize the agent with LiteLLM model
        agent = Agent(
            name="NetBoxComplianceChecker",
            instructions=SYSTEM_INSTRUCTIONS,
            model=LitellmModel(
                model=model,
                api_key=api_key or os.getenv("API_KEY"),
            ),
            mcp_servers=[server],
        )
        
        # Prepare the initial message
        initial_message = f"""Check this compliance rule: {rule}

Scope: {', '.join(f'{k}={v}' for k, v in scope.items())}"""
        
        if limit:
            initial_message += f"\nLimit: Check up to {limit} objects only (demo mode)"
        
        # Run the agent
        result = await Runner.run(
            starting_agent=agent,
            input=initial_message,
            max_turns=max_steps,
        )
        
        # Get tool call count from the server
        tool_calls = server.tool_call_count if hasattr(server, 'tool_call_count') else 0
        
        # Parse the agent's response with tool count
        return parse_agent_response(result, tool_calls)


def parse_agent_response(response: Any, tool_calls: int = 0) -> Dict[str, Any]:
    """
    Extract minimal information from agent response.
    
    Args:
        response: Raw response from the agent
        tool_calls: Number of tool calls made
    
    Returns:
        Dictionary with raw output and basic metadata
    """
    
    # Get the raw output
    raw_output = str(response.final_output) if hasattr(response, "final_output") else str(response)
    
    # Extract just the status for basic routing
    status = "UNKNOWN"
    if "FAIL" in raw_output.upper():
        status = "FAIL"
    elif "PASS" in raw_output.upper():
        status = "PASS"
    
    return {
        "raw_output": raw_output,
        "status": status,
        "tool_calls": tool_calls,
    }