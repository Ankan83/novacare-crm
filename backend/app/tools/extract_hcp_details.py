"""
Extract HCP Details Tool

Uses the LLM to pull a specialty and/or city out of a free-text reply,
when creating a new HCP record after a failed search. Replaces a naive
comma-split parser that broke on quoted input, punctuation, or replies
that only mentioned one of the two fields.
"""

import json
import logging

from app.services.llm import llm

logger = logging.getLogger(__name__)


PROMPT = """
You are an AI assistant extracting Healthcare Professional details
from a short reply in a CRM conversation.

Return ONLY a valid JSON object. No markdown, no explanation, no code
fences, no quotation marks wrapping the whole response.

Schema:

{{
  "specialty": null,
  "city": null
}}

Rules:
- Extract the medical specialty if mentioned. Normalize a profession
  word to its specialty noun form where obvious
  (e.g. "cardiologist" -> "Cardiology", "she does cardiology" -> "Cardiology").
  If unsure of the exact normalization, just return what the user said.
- Extract the city if mentioned.
- The reply may contain both, just one, or be phrased many ways:
  "Cardiology, Noida", "she's a cardiologist based in Noida",
  "just Cardiology", "Noida", or even wrapped in stray quote marks
  like "\\"Cardiology, Noida\\"".
- Strip any quotation marks, surrounding punctuation, or extra words —
  return only the clean value itself (e.g. "Noida", not "Noida\\"" or
  "in Noida").
- If a field isn't mentioned at all in this reply, return null for it —
  do not guess or invent a value.

Reply:

{message}
"""


def extract_hcp_details(message: str) -> dict:
    """
    Extract {"specialty": ..., "city": ...} from a free-text reply.
    Either field may be null if not mentioned in this particular reply.
    """

    response = llm.invoke(
        PROMPT.format(message=message)
    )

    content = response.content.strip()  # type: ignore

    json_start = content.find("{")
    json_end = content.rfind("}")

    if json_start == -1 or json_end == -1:
        raise ValueError(
            f"LLM did not return valid JSON:\n{content}"
        )

    content = content[json_start : json_end + 1]

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Failed to parse LLM JSON response:\n{content}"
        ) from exc

    for key in ("specialty", "city"):
        value = data.get(key)

        if isinstance(value, str):
            # Belt-and-suspenders cleanup in case a stray quote or
            # punctuation slips through despite the prompt instruction.
            value = value.strip().strip("\"'").strip()
            data[key] = value or None
        else:
            data[key] = None

    return data