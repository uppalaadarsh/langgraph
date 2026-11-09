"""
tickets.py — Ticket Storage

Saves tickets to a JSON file so they persist
across app restarts.

Tickets are stored at: tickets_data.json
"""

import json
import random
import os
from datetime import datetime


# ─────────────────────────────────────────────
# File path for ticket storage
# ─────────────────────────────────────────────

TICKETS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "tickets_data.json"
)


# ─────────────────────────────────────────────
# Load tickets from file
# ─────────────────────────────────────────────

def _load_tickets() -> list:
    """Load all tickets from the JSON file."""

    if not os.path.exists(TICKETS_FILE):
        return []

    try:
        with open(TICKETS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


# ─────────────────────────────────────────────
# Save tickets to file
# ─────────────────────────────────────────────

def _save_tickets(tickets: list):
    """Write all tickets to the JSON file."""

    with open(TICKETS_FILE, "w") as f:
        json.dump(tickets, f, indent=2)


# ─────────────────────────────────────────────
# Create a new ticket
# ─────────────────────────────────────────────

def create_new_ticket(
    summary: str,
    priority: str = "medium"
) -> dict:
    """
    Create and save a new support ticket.

    Returns the created ticket dict.
    """

    ticket_id = f"IT-{random.randint(1000, 9999)}"

    ticket = {
        "ticket_id": ticket_id,
        "summary": summary,
        "priority": priority,
        "status": "open",
        "created_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    }

    tickets = _load_tickets()
    tickets.append(ticket)
    _save_tickets(tickets)

    return ticket


# ─────────────────────────────────────────────
# Get all tickets
# ─────────────────────────────────────────────

def get_all_tickets() -> list:
    """Return all tickets from storage."""

    return _load_tickets()


# ─────────────────────────────────────────────
# Get open tickets
# ─────────────────────────────────────────────

def get_open_tickets() -> list:
    """Return only open tickets."""

    tickets = _load_tickets()

    return [
        t for t in tickets
        if t["status"] == "open"
    ]


# ─────────────────────────────────────────────
# Close a ticket
# ─────────────────────────────────────────────

def close_ticket(ticket_id: str) -> bool:
    """
    Mark a ticket as closed.
    Returns True if found, False otherwise.
    """

    tickets = _load_tickets()

    for ticket in tickets:
        if ticket["ticket_id"] == ticket_id:
            ticket["status"] = "closed"
            _save_tickets(tickets)
            return True

    return False


# ─────────────────────────────────────────────
# Clear all tickets
# ─────────────────────────────────────────────

def clear_all_tickets():
    """Delete all tickets."""

    _save_tickets([])

