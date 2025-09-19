"""
System prompts for the compliance checking agent.

This module contains the core prompting strategy that teaches the LLM how to:
1. Understand NetBox's data model and limitations
2. Iteratively explore data using MCP tools
3. Determine compliance through autonomous reasoning
4. Format findings in a consistent, actionable way

The prompt design favors clarity and explicit examples over complex rules,
allowing the LLM to generalize from patterns rather than follow rigid logic.
"""

# Main system instructions that define the agent's behavior
# This prompt is intentionally concise but covers the essential elements:
#
# 1. DOMAIN KNOWLEDGE: Explicitly states what NetBox can/cannot check
#    This prevents the agent from attempting impossible checks
#
# 2. DECISION FLOW: Three-step process (validate → check → report)
#    Simple logic that the model can follow reliably
#
# 3. OUTPUT FORMAT: Structured markdown with specific sections
#    Ensures consistent, parseable output across different models
#
# 4. CONCRETE EXAMPLE: Shows a failing check with proper formatting
#    More effective than abstract rules for teaching output structure
#
# The prompt does NOT include:
# - Tool descriptions (discovered dynamically via MCP)
# - Complex decision trees (relies on model reasoning)
# - Error handling (managed by the agent framework)
SYSTEM_INSTRUCTIONS = """You check NetBox compliance rules using MCP tools.

Important: NetBox stores network infrastructure data like devices, interfaces, IPs, VLANs, and racks.
It does NOT store: SNMP credentials, passwords, SSH keys, monitoring status, or configuration files.

When given a rule and scope:
1. First determine if the rule can be checked with NetBox data
2. If it cannot (e.g., SNMP credentials), explain this and suggest what CAN be checked
3. If it can be checked, query the relevant objects and report compliance

Format your response as markdown with:
- **Status**: PASS or FAIL
- **Summary**: What was checked and the outcome
- **Findings**: List any non-compliant items (if FAIL)
- **Coverage**: What was examined (e.g., "Checked 4 devices in site DM-Akron")

Example response for a failing check:

## Status: FAIL

## Summary
Checked all devices in site DM-Akron for primary IP addresses. Found 4 devices without primary IPs.

## Findings
- dmi01-akron-rtr01: No primary IPv4 or IPv6
- dmi01-akron-sw01: No primary IPv4 or IPv6
- dmi01-akron-pdu01: No primary IPv4 or IPv6
- Patch Panel 01: No primary IPv4 or IPv6

## Coverage
Examined 4 devices in the DM-Akron site."""

# Educational examples for developers extending this agent
# These demonstrate common compliance patterns in NetBox:

EXAMPLE_SCENARIOS = """
Example 1: Interface IP Assignment Check
Rule: "Every interface should have an assigned IP address"
Approach:
1. Get devices in scope (e.g., site=NYC)
2. For each device, get interfaces
3. For each interface, check if ip_addresses field is populated
4. Report any interface without IPs

Example 2: Device Primary IP Check
Rule: "Every device must have a primary IPv4 or IPv6"
Approach:
1. Get devices in scope (e.g., rack=R01)
2. Check each device's primary_ip4 and primary_ip6 fields
3. Report devices missing both

Example 3: Non-checkable Rule
Rule: "All devices must have SNMP credentials configured"
Response:
This rule cannot be checked as NetBox does not store SNMP credentials.
NetBox can check:
- Device inventory and properties
- IP address assignments
- Interface configurations
- VLAN assignments
- Cable connections
"""

# Advanced prompting techniques to consider for production:
#
# 1. CHAIN-OF-THOUGHT: Add "Let's think step-by-step" to encourage planning
#    Example: "First, list what data you'll need. Then gather it. Finally, assess."
#
# 2. FEW-SHOT LEARNING: Include 2-3 full worked examples in the prompt
#    Shows the exact tool calling sequence for common scenarios
#
# 3. SELF-VERIFICATION: Ask the model to double-check its findings
#    Example: "After gathering data, verify your conclusions before reporting"
#
# 4. PROGRESSIVE REFINEMENT: Start with a sample, then expand if issues found
#    Example: "Check 5 devices first. If any fail, check all devices."
#
# 5. CONFIDENCE SCORING: Request certainty levels
#    Example: "Rate your confidence in this assessment (High/Medium/Low)"
#
# 6. TOOL USE OPTIMIZATION: Guide efficient tool usage
#    Example: "Minimize API calls by using filters effectively"
