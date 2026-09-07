"""
Nova Agent Tools

These tools are exposed to the LangGraph agent.

Database-backed operations such as searching HCPs and
saving interactions are orchestrated by ChatService,
while stateless transformations are handled directly
as LangChain tools.
"""

from langchain_core.tools import tool # type: ignore

from app.tools.build_review import build_review
from app.tools.update_draft import update_draft
from app.tools.extract_interaction import extract_interaction


# ==========================================================
# Extract Interaction
# ==========================================================

@tool
def extract_interaction_tool(
    message: str,
):
    """
    Extract structured CRM interaction fields from
    a natural language conversation.
    """

    return extract_interaction(message)


# ==========================================================
# Update Draft
# ==========================================================

@tool
def update_draft_tool(
    current_draft: dict,
    updates: dict,
):
    """
    Merge extracted fields into the interaction draft.
    """

    return update_draft(
        current_draft=current_draft,
        updates=updates,
    )


# ==========================================================
# Build Review
# ==========================================================

@tool
def build_review_tool(
    draft: dict,
):
    """
    Build the final interaction review shown
    before saving.
    """

    return build_review(
        draft=draft,
    )


TOOLS = [
    extract_interaction_tool,
    update_draft_tool,
    build_review_tool,
]