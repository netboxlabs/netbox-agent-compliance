"""MCP helper module for stdio communication with NetBox MCP server."""

import os
from typing import List, Optional, Dict, Any
from agents.mcp import MCPServerStdio, create_static_tool_filter


class CountingMCPServer(MCPServerStdio):
    """MCP server wrapper that counts tool calls."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tool_call_count = 0
    
    async def call_tool(self, *args, **kwargs) -> Any:
        """Override to count tool calls."""
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
    
    Args:
        mcp_dir: Directory containing the NetBox MCP server
        netbox_url: NetBox instance URL
        netbox_token: NetBox API token
        allowed_tools: List of allowed tool names (defaults to read-only tools)
    
    Returns:
        MCPServerStdio instance configured for NetBox
    """
    
    # Default to read-only tools for safety
    if allowed_tools is None:
        allowed_tools = [
            "netbox_get_objects",
            "netbox_get_object_by_id",
            "netbox_get_changelogs",
        ]
    
    # Expand user directory and verify the MCP server directory exists
    mcp_dir = os.path.expanduser(mcp_dir)
    server_path = os.path.join(mcp_dir, "server.py")
    if not os.path.exists(server_path):
        raise FileNotFoundError(
            f"NetBox MCP server not found at {server_path}. "
            f"Please ensure the server is installed at {mcp_dir}"
        )
    
    # Create the MCP server configuration with counting
    server = CountingMCPServer(
        name="netbox",
        params={
            "command": "uv",
            "args": ["--directory", mcp_dir, "run", "server.py"],
            "env": {
                "NETBOX_URL": netbox_url,
                "NETBOX_TOKEN": netbox_token,
                # Inherit current environment
                **os.environ,
            },
        },
        tool_filter=create_static_tool_filter(allowed_tool_names=allowed_tools),
    )
    
    return server