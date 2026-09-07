"""
Nova LangGraph Workflow

Defines the AI workflow for the CRM.
"""

from langgraph.graph import END, START, StateGraph # type: ignore

from app.agent.nodes import (
    conversation_node,
    review_node,
    save_node,
)


# ==========================================================
# Entry Router
# ==========================================================

def entry_router(state: dict):
    """
    Decide which node should run first.

    Every graph invocation starts from START.
    """

    if state.get("ready_for_confirmation", False):
        return "review"

    return "conversation"


# ==========================================================
# Conversation Router
# ==========================================================

def conversation_router(state: dict):

    if state.get("ready_for_confirmation", False):
        return "review"

    return END


# ==========================================================
# Review Router
# ==========================================================

def review_router(state: dict):

    if state.get("confirmed", False):
        return "save"

    return END


# ==========================================================
# Build Graph
# ==========================================================

builder = StateGraph(dict) # type: ignore

builder.add_node(
    "conversation",
    conversation_node, # type: ignore
)

builder.add_node(
    "review",
    review_node, # type: ignore
)

builder.add_node(
    "save",
    save_node, # type: ignore
)

# START decides where to go
builder.add_conditional_edges(
    START,
    entry_router,
)

builder.add_conditional_edges(
    "conversation",
    conversation_router,
)

builder.add_conditional_edges(
    "review",
    review_router,
)

builder.add_edge(
    "save",
    END,
)

graph = builder.compile()