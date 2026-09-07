"""
Build Review Tool

Creates the final interaction review shown before saving.
"""


def build_review(
    *,
    draft: dict,
) -> str:
    """
    Build a human-readable review of the interaction before saving.
    """

    attendees = draft.get("attendees") or []
    attendees_text = ", ".join(attendees) if attendees else "Only You"

    topics = draft.get("topics") or []
    topics_text = ", ".join(topics) if topics else "-"

    review = f"""
Interaction Review

Healthcare Professional
-----------------------
{draft.get("hcp_name", "-")}

Interaction Type
----------------
{draft.get("interaction_type", "-")}

Date
----
{draft.get("interaction_date", "-")}

Subject
-------
{draft.get("subject", "-")}

Attendees
---------
{attendees_text}

Topics
------
{topics_text}

Notes
-----
{draft.get("notes", "-")}

Sentiment
---------
{(draft.get("sentiment") or "neutral").capitalize()}

Follow-up
---------
{draft.get("follow_up", "-")}
"""

    return review.strip()