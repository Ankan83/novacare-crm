"""
Search HCP Tool

Provides database lookup functionality for Nova.
"""

import re

from sqlalchemy import select # type: ignore
from sqlalchemy.orm import Session # type: ignore

from app.models.hcp import HCP

_DOCTOR_TITLE_PATTERN = re.compile(r"(?<!\w)(?:doctor|dr)\.?(?!\w)")
_NON_WORD_PATTERN = re.compile(r"[^\w\s]")


def normalize_name(name: str) -> str:
    """
    Normalize doctor names for fuzzy matching.

    Examples

    Dr Rajesh Sharma
    Dr. Rajesh Sharma
    Doctor Rajesh Sharma

    ↓

    rajesh sharma
    """

    name = name.lower().strip()

    # Remove doctor titles
    name = _DOCTOR_TITLE_PATTERN.sub("", name)

    # Remove punctuation
    name = _NON_WORD_PATTERN.sub("", name)

    # Collapse spaces
    name = " ".join(name.split())

    return name


def search_hcp(
    *,
    db: Session,
    doctor_name: str,
) -> dict:
    """
    Search for healthcare professionals matching a doctor name.

    Returns:
        {
            "found": bool,
            "count": int,
            "multiple": bool,
            "query": str,
            "hcps": [...]
        }
    """

    normalized = normalize_name(doctor_name)
    if not normalized:
        return {
            "found": False,
            "count": 0,
            "multiple": False,
            "query": doctor_name,
            "hcps": [],
        }

    # Search matching is intentionally kept in Python because normalization
    # removes titles and punctuation. Select only the fields needed for the
    # response instead of constructing full ORM entities.
    results = db.execute(
        select(
            HCP.id,
            HCP.full_name,
            HCP.specialty,
            HCP.organization,
            HCP.city,
        )
    ).all()

    matches = []

    for hcp in results:
        db_name = normalize_name(hcp.full_name)

        if normalized in db_name:
            matches.append(
                {
                    "id": hcp.id,
                    "name": hcp.full_name,
                    "specialty": hcp.specialty,
                    "organization": hcp.organization,
                    "city": hcp.city,
                }
            )

    matches = matches[:5]

    return {
        "found": len(matches) > 0,
        "count": len(matches),
        "multiple": len(matches) > 1,
        "query": doctor_name,
        "hcps": matches,
    }