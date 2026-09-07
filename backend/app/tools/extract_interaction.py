"""
Interaction Extraction Tool

Uses the LLM to convert free-text conversations into
structured CRM interaction fields.
"""

import calendar
import json
import logging
import re
from datetime import datetime, timedelta

import dateparser  # type: ignore

from app.services.llm import llm

logger = logging.getLogger(__name__)


PROMPT = """
You are an AI assistant that extracts structured CRM interaction information.

Return ONLY a valid JSON object.
Do NOT include markdown.
Do NOT include explanations.
Do NOT wrap the JSON in code fences.

Schema:

{{ 
  "hcp_name": null,
  "hcp_organization": null,
  "hcp_city": null,
  "hcp_specialty": null,
  "interaction_date": null,
  "interaction_type": null,
  "subject": null,
  "notes": null,
  "duration_minutes": null,
  "attendees": [],
  "topics": [],
  "sentiment": null,
  "sentiment_reason": null,
  "follow_up": null
}} 

Extraction Rules:

0. Corrections
- The message may be a correction to a field already discussed, phrased as
  an instruction. Corrections can use MANY different sentence patterns —
  do not rely on a single keyword. Examples of patterns that ALL mean
  "the new value of this field is Y":
    - "change the interaction date to last Monday"
    - "the date was last Wednesday"
    - "date last Wednesday"
    - "actually it was Dr. Mehta"
    - "update the subject to X"
    - "make it a Call instead"
    - "it should be 45 minutes not 30"
    - "interaction type Meeting"
  In general: whenever a field name (or an obvious synonym like "doctor"
  for HCP, "type" for interaction_type) appears near a value, with or
  without connecting words like "to"/"was"/"is"/"should be", treat that
  value as the new value for that field. Do not require the connector
  word "to" specifically — "was", "is", or no connector at all (just the
  field name followed directly by the value) all count equally.
- A SINGLE message may contain corrections to MULTIPLE fields at once,
  e.g. "change the doctor to Dr. Sandeep Sharma, make it a Meeting instead
  of a Call, and the date should be last Wednesday" or "change the doctor
  name to Dr. Sandeep Sharma and interaction type to Meeting and date was
  last wednesday". Extract EVERY field mentioned, using whatever connector
  word (or none) that particular clause happens to use — do not stop after
  the first one or two just because later clauses use a different
  connector word than earlier ones. Go through the message field by field
  (HCP, date, type, subject, notes, duration, attendees, topics) and check
  each one individually before finalizing the JSON, even if the message is
  short or uses inconsistent phrasing between clauses.

1. HCP
- Extract only ONE primary Healthcare Professional.
- Do NOT include the HCP in attendees.
- Also extract the hospital/clinic/organization the HCP is affiliated
  with, if mentioned (e.g. "Fortis Hospital, Noida", "Apollo Hospital").
  Extract it exactly as stated, into "hcp_organization". If no
  organization is mentioned, return null for this field.
- If the organization phrase includes a city after a comma (e.g.
  "Fortis Hospital, Noida", "Max Hospital, Gurugram"), ALSO extract
  that city separately into "hcp_city". If the message mentions the
  city some other way, extract it there too. If no city is mentioned
  or inferable, return null.
- If the message mentions the HCP's specialty or medical field, in any
  form (e.g. "cardiologist Dr. Mehta", "she's an endocrinologist",
  "Dr. Rao, a pediatrician"), extract it into "hcp_specialty",
  normalized to the specialty noun form (e.g. "cardiologist" ->
  "Cardiology"). Most messages won't mention this at all — if it's not
  there, return null. Do not guess a specialty from the topic of the
  interaction (e.g. discussing asthma treatment does NOT imply the HCP
  is a pulmonologist) — only extract it if the message actually states
  the doctor's specialty directly.

2. Interaction Date
- Extract the date the interaction took place, in ANY form the user gives it
  (e.g. "today", "yesterday", "last Monday", "2 days ago", "on 5th July", "July 5",
  "first Monday of last month", "last Friday of last month").
- Time-of-day-only phrases like "this morning", "this afternoon", "this evening",
  "tonight" implicitly mean TODAY. Extract these as "today" (not the time-of-day
  phrase itself), since they answer "when did this happen" just as clearly as
  saying "today" would.
- Compound expressions combining a week/weekday reference with a relative
  month (e.g. "first Monday of last month", "last month's first week
  Monday", "last Friday of last month") should be extracted EXACTLY as the
  user phrased them, word for word. Do not simplify, reorder, or drop any
  part of the phrase — the ordinal, the weekday, and the month reference
  are all needed to resolve the actual date correctly downstream.
- If the message is a short, direct answer to a question like
  "when did the interaction happen" (e.g. "today", "yesterday", "last week"),
  extract that phrase as the date exactly as given — do not discard it just
  because it's relative rather than an absolute date.
- If the message is a correction, e.g. "change the date to last Monday" or
  "actually it happened yesterday, not today", extract the NEW date mentioned
  ("last Monday" / "yesterday") — this is a real date value, not an
  instruction to ignore.
- Return the value as the user expressed it (e.g. "today", "yesterday",
  "5 July 2026"). Do not attempt to compute the actual calendar date yourself.
- If no date is mentioned at all, return null.

3. Interaction Type
- These four categories cover most interactions — use them when they fit:
  "Meeting", "Call", "Email", "Conference"
  - "talked to", "phoned", "spoke on the phone" -> Call
  - "met with", "visited", "stopped by", "in-person" -> Meeting
  - "emailed", "sent a message", "wrote to" -> Email
  - "at the congress", "at the booth", "conference", "symposium" -> Conference
- If the user states a MORE SPECIFIC type that isn't one of these four
  (e.g. "site visit", "webinar", "in-person discussion", "product demo"),
  extract exactly what they said instead of forcing it into one of the
  four categories — this field is not a fixed enum, so their specific
  wording should be preserved.
- If the message is a short, direct answer to a question like
  "what type of interaction was it" (e.g. a single word or short phrase
  such as "call", "it was a meeting", "email", or something more specific
  like "site visit"), extract that value directly.
- If truly ambiguous or not mentioned at all, return null. Do not guess
  randomly.

4. Subject
- Generate a concise business-friendly title describing the TOPIC discussed
  (not the interaction type, e.g. do not title it "Meeting" or "Call").
- Maximum 8 words.
- Avoid generic, content-free titles like "Discussion" or "Update".

Good examples:
- Ozempic product discussion
- Diabetes therapy follow-up
- Quarterly relationship review
- Product availability discussion
- CME planning discussion

5. Notes
- Summarize the discussion in one or two concise sentences.
- Preserve important business context.

6. Attendees
- Include only additional participants.
- Exclude the Healthcare Professional.

7. Topics
- Extract products, therapies, diseases, campaigns, brands, or discussion themes.
- Always return an array.

8. Sentiment
- IMPORTANT: this may be a short follow-up message in an ongoing
  conversation (e.g. just answering "when did this happen?" with "yesterday").
  Only extract a sentiment value if THIS message itself contains an actual
  cue about how the interaction went. If this message says nothing about
  tone/outcome (e.g. it's just a date, a name, a duration, or any other
  unrelated detail), return null for sentiment — do NOT default to
  "neutral" just because this particular message lacks tone information.
  A null here means "no new information", not "the interaction was neutral" —
  sentiment may already have been correctly captured from an earlier
  message, and returning "neutral" here would incorrectly overwrite it.
- If the user directly states how the interaction went, in their own words
  (e.g. "the discussion was positive", "overall it went really well", "a
  very productive meeting", "he was unhappy with it", "not satisfied"),
  ALWAYS honor that stated sentiment directly — do not override it with a
  more cautious inference from other details in the message.
- Otherwise, if this message DOES describe the interaction itself, infer
  from behavioral cues:
  - positive → interest, agreement, appreciation, productive meeting, willingness to prescribe/adopt
  - negative → objection, dissatisfaction, rejection, complaint, concern
  - neutral → informational discussion with no clear positive or negative signal
- Return EXACTLY one of: "positive", "negative", "neutral", or null —
  lowercase, no extra words like "very" or "mostly", and no punctuation.

9. Duration
Return only the number of minutes.

Example:
30

NOT

"30 minutes"

10. Unknown values
- Unknown scalar values should be null.
- attendees and topics must always be arrays (empty if none).

Conversation:

{message}
"""


# Canonical interaction_type values and a small lookup table to catch
# near-miss phrasings the LLM might still produce despite the prompt
# instructions (defense in depth, not a replacement for the prompt fix).
_CANONICAL_INTERACTION_TYPES = {
    "meeting": "Meeting",
    "call": "Call",
    "email": "Email",
    "conference": "Conference",
}

_INTERACTION_TYPE_ALIASES = {
    "meet": "Meeting",
    "met": "Meeting",
    "visit": "Meeting",
    "visited": "Meeting",
    "in-person": "Meeting",
    "in person": "Meeting",
    "phone": "Call",
    "phone call": "Call",
    "called": "Call",
    "call phone": "Call",
    "e-mail": "Email",
    "mail": "Email",
    "emailed": "Email",
    "congress": "Conference",
    "symposium": "Conference",
    "booth": "Conference",
    "convention": "Conference",
}


def _normalize_interaction_type(value):
    """
    Normalize a free-text interaction_type. Common phrasings map to
    clean canonical labels (Meeting/Call/Email/Conference); anything
    else is accepted as-is (title-cased), since the DB column is a
    plain string with no enum constraint — there's no reason to
    silently discard a specific type the user actually stated
    (e.g. "In-Person Discussion", "Site Visit", "Webinar").
    """

    if not value:
        return None

    key = value.strip().lower()

    if key in _CANONICAL_INTERACTION_TYPES:
        return _CANONICAL_INTERACTION_TYPES[key]

    if key in _INTERACTION_TYPE_ALIASES:
        return _INTERACTION_TYPE_ALIASES[key]

    combined_aliases = {
        **_CANONICAL_INTERACTION_TYPES,
        **_INTERACTION_TYPE_ALIASES,
    }

    # Words that don't carry meaning on their own — if an alias match
    # plus these is ALL that's in the key (e.g. "it was a call"), it's
    # safe to collapse to the canonical type. If something else remains
    # (e.g. "discussion" in "in-person discussion"), the user is stating
    # a more specific type and it should be preserved, not collapsed.
    filler_words = {
        "it", "was", "a", "an", "the", "on", "over", "via", "by",
        "just", "quick", "short", "brief",
    }

    for alias, canonical in combined_aliases.items():
        if alias in key:
            remainder = re.sub(r"[^\w\s-]", " ", key.replace(alias, " "))
            remainder_words = [
                w for w in remainder.split() if w not in filler_words
            ]
            if not remainder_words:
                return canonical

    # No safe alias match — this is a specific type the user stated
    # that just isn't one of our common categories. Accept it as-is
    # rather than discarding it; clean up spacing/hyphens and title-case
    # it for consistent display (e.g. "in-person discussion" ->
    # "In-Person Discussion").
    cleaned = re.sub(r"\s+", " ", value.strip())
    return cleaned.title()


_WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


_ORDINALS = {
    "first": 1,
    "second": 2,
    "third": 3,
    "fourth": 4,
    "fifth": 5,
    "last": -1,
}


def _month_reference(text: str, today: datetime):
    """
    Resolve "last month" / "this month" / "next month" to a (year, month)
    tuple. Returns None if no such phrase is present.
    """

    t = text.lower()

    if "last month" in t:
        year, month = today.year, today.month - 1
        if month == 0:
            month, year = 12, year - 1
        return year, month

    if "next month" in t:
        year, month = today.year, today.month + 1
        if month == 13:
            month, year = 1, year + 1
        return year, month

    if "this month" in t:
        return today.year, today.month

    return None


def _ordinal_weekday(text: str):
    """
    Find phrases like "first Monday", "first week Monday", "last Friday"
    (ordinal + weekday). Returns (ordinal, weekday_index) or None.
    "last" as an ordinal means "the last such weekday in the month".
    """

    t = text.lower()

    match = re.search(
        r"\b(first|second|third|fourth|fifth|last)\s+"
        r"(?:week\s*(?:of)?\s*)?"
        r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        t,
    )

    if not match:
        return None

    ordinal_word, weekday_name = match.groups()

    return _ORDINALS[ordinal_word], _WEEKDAYS[weekday_name]


def _resolve_ordinal_weekday_of_month(text: str):
    """
    Resolve compound expressions like "first Monday of last month",
    "last month's first week Monday", "last Friday of last month".

    Requires BOTH a month reference (last/this/next month) AND an
    ordinal+weekday to be present — otherwise returns None so the
    simpler _resolve_relative_weekday can handle plain "last Friday"
    style phrases without a month reference.
    """

    today = datetime.now()

    month_ref = _month_reference(text, today)
    ordinal_info = _ordinal_weekday(text)

    if not month_ref or not ordinal_info:
        return None

    year, month = month_ref
    ordinal, weekday = ordinal_info

    _, days_in_month = calendar.monthrange(year, month)

    matches = [
        datetime(year, month, day)
        for day in range(1, days_in_month + 1)
        if datetime(year, month, day).weekday() == weekday
    ]

    if not matches:
        return None

    if ordinal == -1:  # "last <weekday> of <month>"
        return matches[-1]

    index = ordinal - 1

    if index < len(matches):
        return matches[index]

    return None


def _resolve_relative_weekday(text: str):
    """
    Resolve phrases like "last Friday", "next Monday", "this Wednesday"
    with plain date arithmetic. dateparser has proven unreliable for
    this exact phrase pattern ("last <weekday>" reliably returns None
    in this environment), so we handle it deterministically ourselves
    instead of depending on it for this case.

    Returns a datetime, or None if the text doesn't match this pattern.
    """

    match = re.search(
        r"\b(last|next|this)\s+"
        r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        text.strip().lower(),
    )

    if not match:
        return None

    modifier, weekday_name = match.groups()
    target_weekday = _WEEKDAYS[weekday_name]

    today = datetime.now()
    today_weekday = today.weekday()

    if modifier == "last":
        delta = (today_weekday - target_weekday) % 7
        delta = delta or 7  # "last Friday" said on a Friday means a week ago
        result = today - timedelta(days=delta)

    elif modifier == "next":
        delta = (target_weekday - today_weekday) % 7
        delta = delta or 7  # "next Friday" said on a Friday means a week ahead
        result = today + timedelta(days=delta)

    else:  # "this"
        delta = (target_weekday - today_weekday) % 7
        result = today + timedelta(days=delta)

    return result


_TIME_OF_DAY_TODAY_PATTERN = re.compile(
    r"\b(this morning|this afternoon|this evening|tonight)\b",
    re.IGNORECASE,
)

_RELATIVE_DAY_PATTERN = re.compile(
    r"\b(?P<amount>\d+)\s+(?P<unit>day|days|week|weeks)\s+ago\b",
    re.IGNORECASE,
)


def _resolve_relative_days(text: str):
    """Resolve numeric relative dates independently of the LLM."""
    normalized = text.strip().lower()
    today = datetime.now()

    if re.search(r"\byesterday\b", normalized):
        return today - timedelta(days=1)

    if re.search(r"\btoday\b", normalized):
        return today

    match = _RELATIVE_DAY_PATTERN.search(normalized)
    if not match:
        return None

    amount = int(match.group("amount"))
    multiplier = 7 if match.group("unit").lower().startswith("week") else 1
    return today - timedelta(days=amount * multiplier)


def _mentions_time_of_day_today(message: str) -> bool:
    """
    Deterministic fallback check: does the raw message contain a
    time-of-day phrase that implicitly means "today"? Used as a safety
    net independent of the LLM, since it's proven inconsistent at
    catching this phrase when it's buried inside a long, detail-dense
    message alongside many other extractable fields.
    """

    return bool(_TIME_OF_DAY_TODAY_PATTERN.search(message))


def extract_interaction(message: str) -> dict:
    """
    Extract structured CRM interaction fields from a free-text conversation.
    """

    response = llm.invoke(
        PROMPT.format(
            message=message,
        )
    )

    content = response.content.strip()  # type: ignore

    # Extract only the JSON object returned by the LLM.
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

    # Normalize interaction date
    interaction_date = data.get("interaction_date")

    # Safety net: resolve common relative dates from the raw message before
    # relying on the LLM's interpretation. This prevents a missing or
    # paraphrased LLM date from turning a clear user answer into a follow-up.
    raw_relative_date = _resolve_relative_days(message)
    if raw_relative_date:
        interaction_date = raw_relative_date.strftime("%Y-%m-%d")

    # Safety net: if the LLM didn't extract a date at all, but the raw
    # message clearly contains a time-of-day phrase implying "today"
    # (e.g. "this morning"), use that instead of asking the user a
    # question they already answered.
    if not interaction_date and _mentions_time_of_day_today(message):
        interaction_date = "today"

    # Second safety net: the LLM sometimes extracts the time-of-day
    # phrase itself ("this morning") instead of converting it to "today"
    # as instructed. dateparser can't resolve a bare time-of-day phrase
    # into a date at all, so normalize the VALUE here too, regardless
    # of whether the LLM followed the conversion instruction.
    if interaction_date and _TIME_OF_DAY_TODAY_PATTERN.search(interaction_date):
        interaction_date = "today"

    if interaction_date and not raw_relative_date:
        # Order matters: try the most specific resolver first.
        # 1. Compound expressions like "first Monday of last month"
        # 2. Simple relative weekdays like "last Friday"
        # 3. dateparser, for everything else (absolute dates, "today",
        #    "2 days ago", etc. — all confirmed working in this environment)
        parsed_date = _resolve_ordinal_weekday_of_month(interaction_date)

        if not parsed_date:
            parsed_date = _resolve_relative_weekday(interaction_date)

        if not parsed_date:
            parsed_date = dateparser.parse(
                interaction_date,
                settings={
                    # If a date is ambiguous (e.g. just "5th"), prefer a date
                    # in the past rather than the future — interactions are
                    # logged after they happen.
                    "PREFER_DATES_FROM": "past",
                    "RETURN_AS_TIMEZONE_AWARE": False,
                },
            )

        if not parsed_date:
            # Retry with plain defaults before giving up.
            parsed_date = dateparser.parse(interaction_date)

        logger.info(
            f"[date normalize] input={interaction_date!r} -> "
            f"parsed={parsed_date!r}"
        )

        if parsed_date:
            data["interaction_date"] = parsed_date.strftime(
                "%Y-%m-%d"
            )
        else:
            # Couldn't confidently resolve it — leave null rather than
            # storing an unparsed string, so the conversation node
            # re-asks instead of silently saving garbage.
            data["interaction_date"] = None

    # Normalize interaction type
    data["interaction_type"] = _normalize_interaction_type(
        data.get("interaction_type")
    )

    # Ensure array fields always exist
    data["attendees"] = data.get("attendees") or []
    data["topics"] = data.get("topics") or []

    # Normalize duration
    duration = data.get("duration_minutes")

    if isinstance(duration, str):
        digits = "".join(ch for ch in duration if ch.isdigit())
        data["duration_minutes"] = (
            int(digits) if digits else None
        )

    # Normalize sentiment
    valid_sentiments = {
        "positive",
        "neutral",
        "negative",
    }

    sentiment = data.get("sentiment")

    if sentiment:
        sentiment = sentiment.lower().strip().rstrip(".")

    if sentiment in valid_sentiments:
        data["sentiment"] = sentiment
    elif sentiment and "positive" in sentiment:
        # Catches "very positive", "mostly positive", "quite positive", etc.
        data["sentiment"] = "positive"
    elif sentiment and "negative" in sentiment:
        data["sentiment"] = "negative"
    elif sentiment:
        # The LLM found SOME sentiment-ish text but it didn't map cleanly —
        # it did detect something, so "neutral" is a genuine reading here.
        data["sentiment"] = "neutral"
    else:
        # No sentiment mentioned in THIS message at all. Leave as None so
        # update_draft skips it and doesn't overwrite a sentiment that was
        # already correctly established in an earlier turn. The "default
        # to neutral if never set" business rule belongs at review/save
        # time, not here.
        data["sentiment"] = None

    return data