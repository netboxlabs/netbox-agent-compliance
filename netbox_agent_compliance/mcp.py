"""
MCP helper module for stdio communication with NetBox MCP server.

This module handles the critical connection between the agent and NetBox:
- Spawns the NetBox MCP server as a subprocess
- Establishes secure stdio communication (no network exposure)
- Filters available tools for safety (read-only by default)
- Tracks metrics like tool call counts

MCP (Model Context Protocol) is the standard way to give LLMs access to
external tools and data sources in a controlled, auditable manner.
"""

import os
from typing import List, Optional, Any
from agents.mcp import MCPServerStdio, create_static_tool_filter


class CountingMCPServer(MCPServerStdio):
    """
    MCP server wrapper that counts tool calls for metrics.

    This simple wrapper helps track how many NetBox API calls the agent makes,
    which is useful for:
    - Understanding agent efficiency
    - Debugging excessive tool use
    - Showing users the work performed
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tool_call_count = 0

    async def call_tool(self, *args, **kwargs) -> Any:
        """Override to count tool calls while preserving functionality."""
        self.tool_call_count += 1
        return await super().call_tool(*args, **kwargs)


def create_mcp_server(
    mcp_dir: str,
    netbox_url: str,
    netbox_token: str,
    allowed_tools: Optional[List[str]] = None,
) -> MCPServerStdio:
    """
    Create an MCP server connection to the NetBox MCP server.

    This function sets up the critical bridge between the LLM agent and NetBox:
    1. Spawns the NetBox MCP server as a subprocess
    2. Passes NetBox credentials via environment variables (never in args)
    3. Filters tools to ensure only safe operations are exposed
    4. Returns a server handle that the agent can use

    The stdio approach (stdin/stdout) is used for security:
    - No network ports opened
    - Process isolation
    - Clear parent-child relationship

    Args:
        mcp_dir: Directory containing the NetBox MCP server
        netbox_url: NetBox instance URL
        netbox_token: NetBox API token
        allowed_tools: List of allowed tool names (defaults to read-only tools)

    Returns:
        MCPServerStdio instance configured for NetBox
    """

    # Default to read-only tools for safety
    # These tools can fetch data but cannot modify NetBox
    # This is crucial for compliance checking - we observe but don't change
    if allowed_tools is None:
        allowed_tools = [
            "netbox_get_objects",  # List objects with filters
            "netbox_get_object_by_id",  # Get specific object details
            "netbox_get_changelogs",  # View change history
            "netbox_search_objects",  # Search objects (v1.0.0+)
        ]

    # Expand user directory and verify the MCP server directory exists
    mcp_dir = os.path.expanduser(mcp_dir)
    pyproject_path = os.path.join(mcp_dir, "pyproject.toml")
    if not os.path.exists(pyproject_path):
        raise FileNotFoundError(
            f"NetBox MCP server not found at {mcp_dir}. "
            f"Please ensure the netbox-mcp-server is installed at {mcp_dir}"
        )

    # Create the MCP server configuration
    # Key design decisions:
    # - Use 'uv run' for consistent Python environment management
    # - Pass credentials via env vars (more secure than CLI args)
    # - Filter tools to prevent accidental modifications
    # - Wrap in our counting class for metrics
    server = CountingMCPServer(
        name="netbox",
        params={
            # Command to spawn the MCP server subprocess
            "command": "uv",
            "args": ["--directory", mcp_dir, "run", "netbox-mcp-server"],
            # Environment variables for the subprocess
            "env": {
                "NETBOX_URL": netbox_url,
                "NETBOX_TOKEN": netbox_token,
                # Inherit current environment for PATH, etc.
                **os.environ,
            },
        },
        # Critical: Filter tools to only allow safe operations
        # This prevents the agent from accidentally modifying NetBox data
        tool_filter=create_static_tool_filter(allowed_tool_names=allowed_tools),
    )

    return server


# For developers extending this:
# 1. To use different tools, modify the allowed_tools list
# 2. To use a different MCP server, change the spawn command
# 3. To add authentication, modify the env vars passed
# 4. To track more metrics, extend the CountingMCPServer class
