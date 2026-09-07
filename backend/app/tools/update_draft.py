"""
Update Draft Tool

Responsible for updating the interaction draft.
"""

from copy import deepcopy


def update_draft(
    *,
    current_draft: dict,
    updates: dict,
) -> dict:
    """
    Merge new information into the interaction draft.

    Returns
    -------
    {
        "draft": ...,
        "highlighted_fields": [...]
    }
    """

    draft = deepcopy(current_draft)
    highlighted_fields = []

    for field, value in updates.items():

        # Ignore unknown values
        if value is None:
            continue

        # Normalize strings
        if isinstance(value, str):
            value = value.strip()

            if (
                value == ""
                or value.lower() in {"null", "none", "unknown", "n/a"}
            ):
                continue

        # Ignore empty lists
        if isinstance(value, list) and not value:
            continue

        # Update only if value actually changed
        if draft.get(field) != value:
            draft[field] = value
            highlighted_fields.append(field)

    return {
        "draft": draft,
        "highlighted_fields": highlighted_fields,
    }