"""CLI interface for NBX Agent Compliance."""

import asyncio
import os
import sys
import time
from typing import Optional
import typer
from rich.console import Console
from rich.markdown import Markdown
from dotenv import load_dotenv
from .agent import run_once

load_dotenv()

app = typer.Typer(
    name="netbox-agent-compliance",
    help="NetBox compliance checking using AI agents and MCP",
)
console = Console()


def main():
    """Main entry point for the CLI."""
    app()


@app.command()
def check(
    rule: str = typer.Argument(
        ...,
        help="Natural language compliance rule to check (e.g., 'every interface should have an assigned ip address')",
    ),
    site: Optional[str] = typer.Option(
        None,
        "--site",
        help="Site name to scope the compliance check",
    ),
    rack: Optional[str] = typer.Option(
        None,
        "--rack",
        help="Rack name to scope the compliance check",
    ),
    device: Optional[str] = typer.Option(
        None,
        "--device",
        help="Device name to scope the compliance check",
    ),
    model: str = typer.Option(
        "openai/gpt-5-nano",
        "--model",
        help="Model to use (e.g., openai/gpt-5-nano, anthropic/claude-sonnet-4-20250514)",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        envvar="API_KEY",
        help="API key for the model provider",
    ),
    netbox_url: str = typer.Option(
        ...,
        "--netbox-url",
        envvar="NETBOX_URL",
        help="NetBox instance URL",
    ),
    netbox_token: str = typer.Option(
        ...,
        "--netbox-token",
        envvar="NETBOX_TOKEN",
        help="NetBox API token",
    ),
    mcp_dir: str = typer.Option(
        ...,
        "--mcp-dir",
        envvar="MCP_SERVER_DIR",
        help="Directory containing the NetBox MCP server (required)",
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        help="Limit the number of objects to check (for demo purposes)",
    ),
    max_steps: int = typer.Option(
        25,
        "--max-steps",
        help="Maximum number of agent steps/tool calls",
    ),
):
    """Run a compliance check against NetBox."""

    # Build scope dictionary
    scope = {}
    if site:
        scope["site"] = site
    if rack:
        scope["rack"] = rack
    if device:
        scope["device"] = device

    if not scope:
        console.print(
            "[red]Error: At least one scope (--site, --rack, or --device) must be specified[/red]"
        )
        sys.exit(1)

    # Validate required environment variables
    if not netbox_url:
        console.print(
            "[red]Error: NETBOX_URL environment variable or --netbox-url option is required[/red]"
        )
        sys.exit(1)

    if not netbox_token:
        console.print(
            "[red]Error: NETBOX_TOKEN environment variable or --netbox-token option is required[/red]"
        )
        sys.exit(1)

    # Expand user directory
    mcp_dir = os.path.expanduser(mcp_dir)

    # Run the compliance check
    console.print(f"[blue]Running compliance check: {rule}[/blue]")
    console.print(
        f"[blue]Scope: {', '.join(f'{k}={v}' for k, v in scope.items())}[/blue]"
    )
    console.print(f"[blue]Model: {model}[/blue]\n")

    start_time = time.time()

    try:
        # Run the async agent
        result = asyncio.run(
            run_once(
                rule=rule,
                scope=scope,
                model=model,
                api_key=api_key,
                mcp_dir=mcp_dir,
                netbox_url=netbox_url,
                netbox_token=netbox_token,
                limit=limit,
                max_steps=max_steps,
            )
        )

        elapsed_time = time.time() - start_time

        # Display the header
        console.print("\n[bold blue]Compliance Check Results[/bold blue]")
        console.print(
            f"[dim]Time: {elapsed_time:.2f}s | Tool calls: {result.get('tool_calls', 0)}[/dim]\n"
        )

        # Display the agent's markdown output directly
        console.print(Markdown(result.get("raw_output", "No output received")))

    except Exception as e:
        console.print(f"[red]Error running compliance check: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
