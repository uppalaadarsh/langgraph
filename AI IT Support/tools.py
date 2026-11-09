"""
tools.py — IT Helpdesk Tools

Each function is decorated with @tool so the LLM
can read its description and decide which to call.
"""

from langchain_core.tools import tool
from langgraph.types import interrupt

from tickets import create_new_ticket, get_all_tickets


# ─────────────────────────────────────────────
# Password Tool
# ─────────────────────────────────────────────

@tool
def password_help() -> str:
    """
    Get troubleshooting instructions
    for password reset issues.

    Use when the user has forgotten their password,
    is locked out, or needs to change their password.
    """

    return """
Password Reset Instructions:

1. Open the company login portal.
2. Click 'Forgot Password'.
3. Verify your registered email.
4. Create a new password.
5. Login again.

If the reset fails, contact IT support.
"""


# ─────────────────────────────────────────────
# VPN Tool
# ─────────────────────────────────────────────

@tool
def vpn_help() -> str:
    """
    Get troubleshooting instructions
    for VPN connection problems.

    Use when the user cannot connect to the VPN,
    has a slow VPN, or VPN keeps disconnecting.
    """

    return """
VPN Troubleshooting:

1. Check internet connection.
2. Restart the VPN application.
3. Verify username and password.
4. Disconnect and reconnect.
5. Restart the computer.

If the issue continues,
a support ticket may be required.
"""


# ─────────────────────────────────────────────
# General IT Tool
# ─────────────────────────────────────────────

@tool
def general_it_help() -> str:
    """
    Get troubleshooting instructions
    for general IT issues.

    Use for slow computer, software crashes,
    printer problems, network issues, or
    any IT issue not related to VPN or passwords.
    """

    return """
General IT Troubleshooting:

1. Restart the application.
2. Restart the computer.
3. Check network connectivity.
4. Check for software updates.
5. Contact IT support if the issue persists.
"""


# ─────────────────────────────────────────────
# Create Ticket Tool (Human-in-the-Loop)
# ─────────────────────────────────────────────

@tool
def create_ticket(
    issue_summary: str,
    priority: str = "medium"
) -> str:
    """
    Create an IT support ticket for
    unresolved issues.

    Use when the user explicitly asks
    to create a support ticket, or when
    the troubleshooting steps did not
    resolve the issue.

    Args:
        issue_summary: Brief description
            of the issue.
        priority: Ticket priority level.
            Options: low, medium, high.
    """

    # --- Human-in-the-Loop ---
    # This pauses the graph and sends
    # the approval request to the user.

    approval = interrupt(
        {
            "question":
                "Do you approve creating "
                "this support ticket?",

            "summary": issue_summary,
            "priority": priority
        }
    )

    # The graph resumes here after
    # the user responds.

    if approval == "yes":

        ticket = create_new_ticket(
            summary=issue_summary,
            priority=priority
        )

        return (
            f"✅ Ticket {ticket['ticket_id']} created "
            f"successfully!\n"
            f"Summary: {issue_summary}\n"
            f"Priority: {priority}"
        )

    else:

        return (
            "❌ Ticket creation cancelled "
            "by user."
        )


# ─────────────────────────────────────────────
# View Tickets Tool
# ─────────────────────────────────────────────

@tool
def view_tickets() -> str:
    """
    View all IT support tickets.

    Use when the user asks to see their tickets,
    check ticket status, or view open issues.
    """

    tickets = get_all_tickets()

    if not tickets:
        return "No tickets found."

    result = "All Support Tickets:\n\n"

    for t in tickets:

        status_icon = (
            "🟢" if t["status"] == "open"
            else "🔴"
        )

        result += (
            f"  {status_icon} {t['ticket_id']} | "
            f"{t['priority'].upper()} | "
            f"{t['summary']} | "
            f"{t['status']} | "
            f"{t['created_at']}\n"
        )

    return result


# ─────────────────────────────────────────────
# All tools list
# ─────────────────────────────────────────────

ALL_TOOLS = [
    password_help,
    vpn_help,
    general_it_help,
    create_ticket,
    view_tickets
]
