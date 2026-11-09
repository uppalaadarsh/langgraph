"""
app.py — Streamlit UI for the IT Helpdesk Agent

Run with:
    streamlit run app.py
"""

import uuid

import streamlit as st

from langgraph.types import Command

from graph import build_graph
from tickets import (
    get_all_tickets,
    close_ticket,
    clear_all_tickets
)


# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="IT Helpdesk Agent",
    page_icon="🛠️",
    layout="centered"
)

st.title("🛠️ AI IT Helpdesk Agent")
st.caption(
    "Powered by LangGraph · "
    "Ask about passwords, VPN, or any IT issue"
)


# ─────────────────────────────────────────────
# Initialize session state
# ─────────────────────────────────────────────

if "graph" not in st.session_state:
    st.session_state.graph = build_graph()

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "pending_approval" not in st.session_state:
    st.session_state.pending_approval = None

if "queued_prompt" not in st.session_state:
    st.session_state.queued_prompt = None


# ─────────────────────────────────────────────
# Shortcuts
# ─────────────────────────────────────────────

graph = st.session_state.graph

config = {
    "configurable": {
        "thread_id": st.session_state.thread_id
    }
}


# ─────────────────────────────────────────────
# Sidebar — Tabs: Controls | Tickets | Graph
# ─────────────────────────────────────────────

with st.sidebar:

    tab_controls, tab_tickets, tab_graph = st.tabs(
        ["💬 Chat", "📋 Tickets", "📊 Graph"]
    )

    # ── Tab 1: Chat Controls ──

    with tab_controls:

        if st.button(
            "🔄 New Conversation",
            use_container_width=True
        ):
            st.session_state.thread_id = str(
                uuid.uuid4()
            )
            st.session_state.chat_history = []
            st.session_state.pending_approval = None
            st.session_state.queued_prompt = None
            st.rerun()

        st.divider()

        st.subheader("💡 Try these queries")

        examples = [
            "My VPN is not connecting.",
            "I forgot my password.",
            "My laptop is very slow.",
            "Create a ticket for my broken monitor.",
            "Show me all open tickets.",
        ]

        for example in examples:
            if st.button(
                example,
                key=f"ex_{example[:20]}",
                use_container_width=True
            ):
                st.session_state.example_query = example
                st.rerun()

        st.divider()

        st.caption(
            f"Thread: `{st.session_state.thread_id[:8]}...`"
        )

    # ── Tab 2: Tickets ──

    with tab_tickets:

        st.subheader("Support Tickets")

        tickets = get_all_tickets()

        if not tickets:
            st.info("No tickets yet. Ask the agent to create one!")

        else:
            # Summary counts
            open_count = sum(
                1 for t in tickets
                if t["status"] == "open"
            )
            closed_count = sum(
                1 for t in tickets
                if t["status"] == "closed"
            )

            col1, col2 = st.columns(2)
            col1.metric("🟢 Open", open_count)
            col2.metric("🔴 Closed", closed_count)

            st.divider()

            # Ticket list
            for ticket in reversed(tickets):

                status_color = (
                    "🟢" if ticket["status"] == "open"
                    else "🔴"
                )

                with st.expander(
                    f"{status_color} {ticket['ticket_id']} — "
                    f"{ticket['summary'][:40]}"
                ):
                    st.markdown(
                        f"**ID:** `{ticket['ticket_id']}`"
                    )
                    st.markdown(
                        f"**Summary:** {ticket['summary']}"
                    )
                    st.markdown(
                        f"**Priority:** {ticket['priority'].upper()}"
                    )
                    st.markdown(
                        f"**Status:** {ticket['status']}"
                    )
                    st.markdown(
                        f"**Created:** {ticket['created_at']}"
                    )

                    if ticket["status"] == "open":
                        if st.button(
                            "Close Ticket",
                            key=f"close_{ticket['ticket_id']}",
                            use_container_width=True
                        ):
                            close_ticket(
                                ticket["ticket_id"]
                            )
                            st.rerun()

            st.divider()

            if st.button(
                "🗑️ Clear All Tickets",
                use_container_width=True
            ):
                clear_all_tickets()
                st.rerun()

    # ── Tab 3: Graph ──

    with tab_graph:

        st.subheader("Agent Graph")

        try:
            graph_png = (
                graph
                .get_graph()
                .draw_mermaid_png()
            )
            st.image(graph_png)
        except Exception:
            st.info(
                "Install graphviz to see "
                "the graph diagram."
            )


# ─────────────────────────────────────────────
# Helper: run the agent and collect results
# ─────────────────────────────────────────────

def run_agent(user_input: str):
    """
    Run a user message through the graph.
    Returns the assistant's final text response.
    If the graph pauses for approval, returns None
    and sets pending_approval in session state.
    """

    events = list(
        graph.stream(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": user_input
                    }
                ]
            },
            config
        )
    )

    # Check if the graph is paused (interrupt)
    state = graph.get_state(config)

    if state.next:
        for task in state.tasks:
            if task.interrupts:
                for intr in task.interrupts:
                    st.session_state.pending_approval = (
                        intr.value
                    )
                    return None

    return _extract_final_response(events)


def resume_agent(decision: str):
    """
    Resume a paused graph with the user's decision.
    Returns the assistant's final text response.
    """

    events = list(
        graph.stream(
            Command(resume=decision),
            config
        )
    )

    st.session_state.pending_approval = None

    return _extract_final_response(events)


def _extract_final_response(events):
    """
    Walk through stream events and return
    the last AI text response.
    """

    final_text = ""

    for step in events:
        for node_name, output in step.items():
            for msg in output.get("messages", []):
                if (
                    hasattr(msg, "content")
                    and msg.content
                    and not getattr(
                        msg, "tool_calls", None
                    )
                ):
                    final_text = msg.content

    return final_text if final_text else None


# ─────────────────────────────────────────────
# Render chat history & Quick Suggestions
# ─────────────────────────────────────────────

for idx, entry in enumerate(st.session_state.chat_history):

    with st.chat_message(entry["role"]):
        st.markdown(entry["content"])

    # If this is the latest assistant message and not waiting on ticket approval,
    # offer Yes / No quick suggestions
    if (
        entry["role"] == "assistant"
        and idx == len(st.session_state.chat_history) - 1
        and not st.session_state.pending_approval
    ):
        st.caption("Suggested replies:")
        btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 2])
        with btn_col1:
            if st.button("👍 Yes, issue is resolved", key=f"sug_yes_{idx}", use_container_width=True):
                st.session_state.queued_prompt = "Yes, that resolved my issue. Thank you!"
                st.rerun()
        with btn_col2:
            if st.button("👎 No, still not working", key=f"sug_no_{idx}", use_container_width=True):
                st.session_state.queued_prompt = "No, that did not work. Please create a support ticket for me."
                st.rerun()


# ─────────────────────────────────────────────
# Handle pending ticket approval
# ─────────────────────────────────────────────

if st.session_state.pending_approval:

    approval = st.session_state.pending_approval

    with st.chat_message("assistant"):

        st.markdown("### 🎫 Ticket Approval Required")

        st.info(
            f"**Summary:** "
            f"{approval.get('summary', 'N/A')}\n\n"
            f"**Priority:** "
            f"{approval.get('priority', 'N/A')}"
        )

        st.markdown(
            f"*{approval.get('question', 'Approve?')}*"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "✅ Approve",
                type="primary",
                use_container_width=True
            ):
                st.session_state.chat_history.append({
                    "role": "user",
                    "content":
                        "✅ Approved ticket creation."
                })

                response = resume_agent("yes")

                if response:
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response
                    })

                st.rerun()

        with col2:
            if st.button(
                "❌ Reject",
                use_container_width=True
            ):
                st.session_state.chat_history.append({
                    "role": "user",
                    "content":
                        "❌ Rejected ticket creation."
                })

                response = resume_agent("no")

                if response:
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response
                    })

                st.rerun()


# ─────────────────────────────────────────────
# Handle example queries & queued suggestion prompts
# ─────────────────────────────────────────────

prompt_to_send = None

if "example_query" in st.session_state:
    prompt_to_send = st.session_state.example_query
    del st.session_state.example_query

elif st.session_state.queued_prompt:
    prompt_to_send = st.session_state.queued_prompt
    st.session_state.queued_prompt = None

if prompt_to_send:

    st.session_state.chat_history.append({
        "role": "user",
        "content": prompt_to_send
    })

    response = run_agent(prompt_to_send)

    if response:
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response
        })

    st.rerun()


# ─────────────────────────────────────────────
# Chat input
# ─────────────────────────────────────────────

if not st.session_state.pending_approval:

    user_input = st.chat_input(
        "Describe your IT issue..."
    )

    if user_input:

        with st.chat_message("user"):
            st.markdown(user_input)

        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = run_agent(user_input)

            if response:
                st.markdown(response)
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response
                })
            else:
                st.rerun()
