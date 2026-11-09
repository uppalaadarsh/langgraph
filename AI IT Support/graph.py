"""
graph.py — LangGraph Agent Graph

Builds the agent loop:
  START → agent → tools_condition?
                    ├── has tool calls → tools → agent (loop)
                    └── no tool calls  → END
"""

import os

from langgraph.graph import (
    StateGraph,
    START,
    END,
    MessagesState
)

from langgraph.prebuilt import (
    ToolNode,
    tools_condition
)

from langgraph.checkpoint.memory import MemorySaver

from langchain_core.messages import SystemMessage

from langchain_openai import ChatOpenAI

from dotenv import load_dotenv

from tools import ALL_TOOLS


# ─────────────────────────────────────────────
# Load environment variables
# ─────────────────────────────────────────────

load_dotenv()


# ─────────────────────────────────────────────
# Create the LLM with tools bound
# ─────────────────────────────────────────────

model = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
    temperature=0
)

model_with_tools = model.bind_tools(ALL_TOOLS)


# ─────────────────────────────────────────────
# System prompt
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """
You are an IT Helpdesk Assistant.

Your job is to help employees with
IT support requests.

You have access to tools for:
- Password reset issues
- VPN connection problems
- General IT troubleshooting
- Creating support tickets

Always use the appropriate tool first
to get troubleshooting instructions.

Then give a short, clear, professional
answer to the user.

If the issue cannot be resolved with
the troubleshooting steps, offer to
create a support ticket.

Do not invent additional technical details.
"""


# ─────────────────────────────────────────────
# Agent node
# ─────────────────────────────────────────────

def agent_node(state: MessagesState):
    """
    Calls the LLM with the conversation history.
    The LLM either calls a tool or responds directly.
    """

    messages = [
        SystemMessage(content=SYSTEM_PROMPT)
    ] + state["messages"]

    response = model_with_tools.invoke(messages)

    return {
        "messages": [response]
    }


# ─────────────────────────────────────────────
# Build the graph
# ─────────────────────────────────────────────

def build_graph():
    """
    Builds and compiles the helpdesk agent graph.

    Returns the compiled graph with a
    MemorySaver checkpointer.
    """

    builder = StateGraph(MessagesState)

    # Add nodes
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(ALL_TOOLS))

    # Add edges
    builder.add_edge(START, "agent")

    builder.add_conditional_edges(
        "agent",
        tools_condition
    )

    builder.add_edge("tools", "agent")

    # Compile with memory for human-in-the-loop
    memory = MemorySaver()

    graph = builder.compile(
        checkpointer=memory
    )

    return graph

