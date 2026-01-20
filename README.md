# NetBox AI Compliance Agent

A lean agent that performs NetBox compliance checks using natural language rules. Built with OpenAI Agents SDK, LiteLLM, and NetBox MCP server.

NetBox is the semantic map for network and infrastructure AI. The [NetBox MCP server](https://github.com/netboxlabs/netbox-mcp-server) makes it easy to build powerful agents atop NetBox's structured context. This agent is a simple example. Clone it, remix it, or simply use it as a bit of inspiration to get started building your own NetBox agents. Be sure to share what you build in the [NetBox Slack](https://netdev.chat/) and on social media so the community can learn together!

Read about this agent in the related [blog post from NetBox Labs](https://netboxlabs.com/blog/build-your-first-netbox-ai-agent-workshop-recap/).

## Features

- **Natural language compliance rules** - Write rules in plain English
- **Flexible scoping** - Check compliance at site, rack, or device level
- **Model agnostic** - Works with OpenAI or Anthropic models via LiteLLM
- **Read-only operations** - Safe, non-destructive compliance checking
- **Minimal implementation** - Clean, simple code (~150 LOC)

## Installation

### Prerequisites

1. Python 3.10 or higher
2. NetBox instance with API access
3. [NetBox MCP server](https://github.com/netboxlabs/netbox-mcp-server) v1.0.0+ installed
4. [uv](https://github.com/astral-sh/uv) installed

### Setup

Start by creating a fork of the repository.

1. Clone this repository:
```bash
git clone https://github.com/netboxlabs/netbox-agent-compliance.git
cd netbox-agent-compliance
```

2. Create virtual environment and install:
```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

3. Set up environment variables:
```bash
export NETBOX_URL="https://your-netbox-instance.com"
export NETBOX_TOKEN="your-netbox-api-token"
export API_KEY="your-openai-or-anthropic-api-key" # Depends on the --model that you use, currently defaults to openai/gpt-5-nano
export MCP_SERVER_DIR="~/netbox-mcp-server"  # Path to NetBox MCP server
```

Or create a `.env` file:
```env
NETBOX_URL=https://your-netbox-instance.com
NETBOX_TOKEN=your-netbox-api-token
API_KEY=your-openai-or-anthropic-api-key
MCP_SERVER_DIR=~/netbox-mcp-server
```

## Usage

### Basic Examples

Check that every interface in a site has an assigned IP address:
```bash
netbox-agent-compliance "every interface should have an assigned ip address" --site "NYC"
```

Check that devices in a rack have primary IPs:
```bash
netbox-agent-compliance "every device should have a primary IPv4 or IPv6" --rack "R01"
```

### Command Options

```bash
netbox-agent-compliance [RULE] [OPTIONS]

Arguments:
  RULE  Natural language compliance rule to check

Options:
  --site TEXT           Site name to scope the compliance check
  --rack TEXT           Rack name to scope the compliance check  
  --device TEXT         Device name to scope the compliance check
  --model TEXT          Model to use (default: openai/gpt-5-nano)
  --api-key TEXT        API key for the model provider [env: API_KEY]
  --netbox-url TEXT     NetBox instance URL [env: NETBOX_URL] (required)
  --netbox-token TEXT   NetBox API token [env: NETBOX_TOKEN] (required)
  --mcp-dir TEXT        Directory containing the NetBox MCP server [env: MCP_SERVER_DIR] (required)
  --limit INT           Limit objects to check (for demos)
  --max-steps INT       Maximum agent steps (default: 25)
```

### Supported Model Providers

Via LiteLLM, you can use various models:

**OpenAI:**
- `openai/gpt-5-nano` (default)
- `openai/gpt-4.1-mini`
- `openai/gpt-4o-mini`
- etc

**Anthropic:**
- `anthropic/claude-sonnet-4-20250514`
- `anthropic/claude-3-7-sonnet-20250219`
- `anthropic/claude-3-5-haiku-20241022`
- etc

### Example Output

```
Running compliance check: every device should have a primary IPv4 or IPv6
Scope: site=DM-Akron
Model: openai/gpt-5-nano

Compliance Check Results
Time: 29.20s | Tool calls: 2

## Status: FAIL

## Summary
Checked all devices in site DM-Akron for a primary IPv4 or IPv6 address. Found that all 4 devices lack any primary IP assignment.

## Findings
- dmi01-akron-rtr01: No primary IPv4 or IPv6
- dmi01-akron-sw01: No primary IPv4 or IPv6
- dmi01-akron-pdu01: No primary IPv4 or IPv6
- Panduit 48-Port Patch Panel (74): No primary IPv4 or IPv6

## Coverage
Examined 4 devices in the DM-Akron site.
```

### Handling Unsupported Rules

When you provide a rule that can't be checked with NetBox data:

```bash
netbox-agent-compliance "all devices must have SNMP credentials configured" --site "DM-Akron"

Compliance Check Results
Time: 19.19s | Tool calls: 0

## Status: FAIL

## Summary
Rule: "all devices must have SNMP credentials configured" cannot be verified using NetBox data. 
NetBox does not store SNMP credentials, passwords, or monitoring configuration. 
Suggest checking SNMP credentials in your credential store or configuration management system.

## Findings
- NetBox cannot verify SNMP credentials existence or validity
- No compliant/non-compliant items can be reported from NetBox data

## Coverage
Scope: site DM-Akron. No SNMP credential verification was performed.
```

## Supported Compliance Checks

The agent can check any compliance rule that maps to NetBox data model:

### ✅ Supported Examples

- IP address assignments to interfaces
- Primary IPv4/IPv6 on devices
- Device platform assignments
- Interface descriptions
- VLAN assignments
- Device locations
- Rack assignments
- Cable connections
- Power connections

### ❌ Not Supported

Rules referencing data outside NetBox core:
- SNMP credentials
- SSH keys
- Monitoring status
- External system integrations

When you provide an unsupported rule, the agent will explain why and suggest alternatives.

## Architecture

The system consists of four minimal modules:

- **cli.py** - Typer-based CLI interface
- **agent.py** - Agent orchestration with LiteLLM and MCP
- **prompts.py** - Minimal system instructions with example output
- **mcp.py** - MCP stdio helper with tool call counting

## Development

### Testing

Test individual compliance checks:
```bash
netbox-agent-compliance "every device should have a primary IPv4 or IPv6" --site "DM-Akron"
```

## Limitations

- **Soft cap of ~25 tool calls** - Very large scopes may not be fully checked
- **Read-only** - No remediation or write operations
- **NetBox core data only** - Custom fields and plugins not supported in MVP

## Contributing

Contributions are welcome! Please submit issues and pull requests.

## License

MIT
