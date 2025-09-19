"""
Agent module for NetBox compliance checking using LiteLLM and MCP.

This module demonstrates the core pattern for building NetBox agents:
1. Establish MCP connection to NetBox for tool access
2. Initialize an LLM agent with model-agnostic support
3. Run an autonomous agent loop that iteratively calls tools
4. Parse and return structured results

The agent operates in a single-run mode (stateless) for simplicity.
"""

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
    Run a single compliance check against NetBox using an autonomous agent loop.

    This function demonstrates the minimal setup needed for a NetBox agent:
    - MCP server provides tool access to NetBox data (read-only for safety)
    - LiteLLM enables model flexibility (OpenAI, Anthropic, etc.)
    - Agent autonomously decides which tools to call and when to stop

    Args:
        rule: Natural language compliance rule (e.g., "every device needs a primary IP")
        scope: Scope dictionary (site, rack, device) to limit the check
        model: Model identifier for LiteLLM (e.g., "openai/gpt-4o", "anthropic/claude-3-sonnet")
        api_key: API key for the model provider
        mcp_dir: Directory containing the NetBox MCP server
        netbox_url: NetBox instance URL
        netbox_token: NetBox API token
        limit: Optional limit on number of objects to check (for demos/testing)
        max_steps: Maximum number of agent steps (prevents runaway loops)

    Returns:
        Dictionary containing compliance check results
    """

    # STEP 1: Establish MCP connection to NetBox
    # The MCP server runs as a subprocess and exposes NetBox data via tools
    # We use stdio communication (stdin/stdout) for security and simplicity
    async with create_mcp_server(
        mcp_dir=mcp_dir,
        netbox_url=netbox_url,
        netbox_token=netbox_token,
    ) as server:
        # Get API key and validate it exists
        final_api_key = api_key or os.getenv("API_KEY")
        if not final_api_key:
            raise ValueError(
                "API key is required. Set API_KEY environment variable or use --api-key option."
            )

        # Set OPENAI_API_KEY to suppress trace warnings
        if not os.getenv("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = final_api_key

        # STEP 2: Initialize the agent with LLM and MCP tools
        # The Agent combines:
        # - System instructions (how to check compliance)
        # - LLM model (via LiteLLM for flexibility)
        # - MCP server connection (provides NetBox tools)
        agent = Agent(
            name="NetBoxComplianceChecker",
            instructions=SYSTEM_INSTRUCTIONS,  # Detailed prompting strategy
            model=LitellmModel(
                model=model,  # Works with any LiteLLM-supported model
                api_key=final_api_key,
            ),
            mcp_servers=[server],  # Agent can now call NetBox tools
        )

        # STEP 3: Prepare the user's request
        # We format the rule and scope into a clear instruction for the agent
        initial_message = f"""Check this compliance rule: {rule}

Scope: {", ".join(f"{k}={v}" for k, v in scope.items())}"""

        if limit:
            initial_message += f"\nLimit: Check up to {limit} objects only (demo mode)"

        # STEP 4: Run the autonomous agent loop
        # The Runner handles the back-and-forth between LLM and tools
        # The agent will:
        # 1. Understand the rule and scope
        # 2. Call MCP tools to fetch NetBox data
        # 3. Iteratively explore until it can determine compliance
        # 4. Stop when complete or at max_turns
        result = await Runner.run(
            starting_agent=agent,
            input=initial_message,
            max_turns=max_steps,  # Safety limit to prevent infinite loops
        )

        # STEP 5: Extract metrics and return results
        # We track tool calls to show how much work the agent did
        tool_calls = server.tool_call_count if hasattr(server, "tool_call_count") else 0

        # Parse and structure the agent's natural language response
        return parse_agent_response(result, tool_calls)


def parse_agent_response(response: Any, tool_calls: int = 0) -> Dict[str, Any]:
    """
    Extract minimal information from agent response.

    This parser is intentionally simple - we let the agent format its own
    output in markdown and just extract the key status for programmatic use.
    This approach keeps the code minimal while giving the LLM full control
    over how to present findings to users.

    Args:
        response: Raw response from the agent
        tool_calls: Number of tool calls made

    Returns:
        Dictionary with raw output and basic metadata
    """

    # Get the raw output - this contains the agent's full markdown report
    raw_output = (
        str(response.final_output)
        if hasattr(response, "final_output")
        else str(response)
    )

    # Extract just the status for basic routing
    # The agent is instructed to always include "PASS" or "FAIL" in its output
    status = "UNKNOWN"
    if "Status: FAIL" in raw_output:
        status = "FAIL"
    elif "Status: PASS" in raw_output:
        status = "PASS"

    return {
        "raw_output": raw_output,  # Full markdown report for display
        "status": status,  # Extracted status for programmatic use
        "tool_calls": tool_calls,  # Metric showing agent's work
    }
