"""
Nova LangGraph Nodes

These nodes implement the business workflow of the AI-first CRM.
"""

from copy import deepcopy

from app.tools.build_review import build_review
from app.tools.extract_interaction import extract_interaction
from app.tools.search_hcp import search_hcp
from app.tools.update_draft import update_draft
from app.tools.save_interaction import save_interaction


# ==========================================================
# Intent helpers
# ==========================================================

_NEW_INTERACTION_PHRASES = {
    "log another interaction",
    "log another",
    "add another interaction",
    "add another",
    "new interaction",
    "start a new interaction",
    "log a new interaction",
    "yes, log another",
    "yes log another",
}

_PREVIOUS_REVIEW_PHRASES = {
    "show me the previous interaction",
    "show me my last interaction",
    "show previous interaction",
    "show last interaction",
    "what was my last interaction",
    "show me the last review",
    "previous review",
    "last review",
    "show my last saved interaction",
    "view this interaction",
    "view the interaction",
    "view last interaction",
}

_SHOW_ALL_PREVIOUS_PHRASES = {
    "show previous interactions",
    "show all previous interactions",
    "show my interactions",
    "show all interactions",
    "list previous interactions",
    "list my interactions",
}

_EDIT_INTERACTION_PHRASES = {
    "edit this interaction",
    "edit the interaction",
    "edit last interaction",
    "edit my last interaction",
    "change this interaction",
}

_MEETING_PREP_PHRASES = {
    "prepare me for my next meeting",
    "prepare for my next meeting",
    "prep me for my next meeting",
    "prepare me for the next meeting",
}


def _wants_show_all_previous(message: str) -> bool:
    text = message.lower().strip()
    return any(phrase in text for phrase in _SHOW_ALL_PREVIOUS_PHRASES)


def _wants_edit_interaction(message: str) -> bool:
    text = message.lower().strip()
    return any(phrase in text for phrase in _EDIT_INTERACTION_PHRASES)


def _wants_meeting_prep(message: str) -> bool:
    text = message.lower().strip()
    return any(phrase in text for phrase in _MEETING_PREP_PHRASES)


def _wants_new_interaction(message: str) -> bool:
    text = message.lower().strip()
    return any(phrase in text for phrase in _NEW_INTERACTION_PHRASES)


def _wants_previous_review(message: str) -> bool:
    text = message.lower().strip()
    return any(phrase in text for phrase in _PREVIOUS_REVIEW_PHRASES)


_CRM_TERMS = {
    "hcp",
    "doctor",
    "dr",
    "interaction",
    "meeting",
    "met",
    "visit",
    "visited",
    "call",
    "called",
    "email",
    "emailed",
    "conference",
    "hospital",
    "clinic",
    "follow-up",
    "followup",
    "subject",
    "notes",
    "date",
    "today",
    "yesterday",
    "tomorrow",
}


def _is_unrelated_first_message(message: str, draft: dict) -> bool:
    """Avoid treating an obvious non-CRM greeting or question as data."""
    if draft:
        return False

    words = set(message.lower().replace("?", "").split())
    return not words.intersection(_CRM_TERMS)


# ==========================================================
# Conversation Node
# ==========================================================


def conversation_node(state: dict) -> dict:
    """
    Main conversation node.

    Responsibilities
    ----------------
    1. Handle "log another interaction" / "show previous interaction" intents
    2. Extract interaction details
    3. Search HCP
    4. Update draft
    5. Decide next question
    """

    db = state["db"]

    message = state["message"]

    draft = deepcopy(state.get("draft", {}))

    if _is_unrelated_first_message(message, draft):
        state.update(
            {
                "draft": draft,
                "highlighted_fields": [],
                "assistant_message": (
                    "I can help log an HCP interaction. Tell me who you "
                    "spoke with, what you discussed, and when it happened."
                ),
                "ready_for_confirmation": False,
                "confirmed": False,
                "current_field": "hcp_name",
            }
        )
        return state

    # ---------------------------------------------
    # Pending new-HCP details: the previous turn offered to create a
    # new HCP and asked for specialty/city. Handle that reply BEFORE
    # any other logic, so it isn't run through interaction extraction.
    # ---------------------------------------------

    if state.get("awaiting_new_hcp_details"):

        state["awaiting_new_hcp_details"] = False

        pending = state.get("pending_new_hcp") or {}

        from app.tools.extract_hcp_details import extract_hcp_details

        try:
            extracted = extract_hcp_details(message)
        except Exception:
            # Extraction itself failed (LLM error, bad JSON, etc.) —
            # ask again rather than crashing the request.
            state["pending_new_hcp"] = pending
            state["awaiting_new_hcp_details"] = True
            state["draft"] = draft
            state["assistant_message"] = (
                "Sorry, I didn't catch that clearly. Could you tell me "
                "the specialty and/or city again?"
            )
            return state

        # A one-word reply such as "Diabetes" can be unambiguous from the
        # conversation state even when the LLM returns null for both fields.
        # Assign it to the sole missing field rather than asking repeatedly.
        missing_before_merge = [
            field for field in ("specialty", "city") if not pending.get(field)
        ]
        if (
            len(missing_before_merge) == 1
            and not extracted.get(missing_before_merge[0])
        ):
            fallback_value = message.strip().strip("\"'.,;: ")
            for prefix in ("in ", "from ", "at "):
                if fallback_value.lower().startswith(prefix):
                    fallback_value = fallback_value[len(prefix):].strip()
                    break
            if fallback_value:
                extracted[missing_before_merge[0]] = fallback_value

        # Merge whatever this reply provided into what we already have.
        # Supports partial answers across multiple turns (e.g. "Cardiology"
        # this turn, "Noida" next turn) rather than requiring both at once.
        if extracted.get("specialty"):
            pending["specialty"] = extracted["specialty"]

        if extracted.get("city"):
            pending["city"] = extracted["city"]

        still_missing = [
            field for field in ("specialty", "city")
            if not pending.get(field)
        ]

        if still_missing:
            # Ask specifically for what's still missing, not the whole
            # thing again.
            state["pending_new_hcp"] = pending
            state["awaiting_new_hcp_details"] = True
            state["draft"] = draft
            state["assistant_message"] = (
                f"Got it. I still need the {' and '.join(still_missing)} "
                "to create this HCP record."
            )
            return state

        from app.tools.create_hcp import create_hcp

        try:
            new_hcp = create_hcp(
                db=db,
                full_name=pending.get("full_name", ""),
                specialty=pending["specialty"],
                organization=pending.get("organization", ""),
                city=pending["city"],
            )
        except Exception:
            state["assistant_message"] = (
                "I ran into an issue creating that HCP record. "
                "Could you try again, or provide the details differently?"
            )
            state["pending_new_hcp"] = pending
            state["awaiting_new_hcp_details"] = True
            state["draft"] = draft
            return state

        draft["hcp_id"] = new_hcp["id"]
        draft["hcp_specialty"] = pending["specialty"]
        draft["hcp_city"] = pending["city"]
        draft.pop("hcp_search_result", None)
        draft.pop("hcp_organization", None)
        state["pending_new_hcp"] = None

        # Go straight to the required-fields check with the updated
        # draft — do NOT fall through into extract_interaction(), since
        # this message is HCP details, not interaction content, and
        # running it through extraction would waste a call and risk
        # merging garbage into the draft.
        return _check_required_fields_and_respond(state, draft, [])

    # ---------------------------------------------
    # Post-save choice: the previous turn just saved an interaction
    # and asked "log another / preview last?". Handle that reply
    # BEFORE any other logic, so a bare "yes"/"no"/"1"/"2" here is
    # never misread as a save confirmation or run through extraction.
    # ---------------------------------------------

    if state.get("awaiting_post_save_choice"):

        state["awaiting_post_save_choice"] = False

        choice = message.lower().strip()

        wants_preview = (
            choice in {"2", "view", "view this interaction"}
            or _wants_previous_review(message)
        )

        wants_edit = _wants_edit_interaction(message)

        wants_show_all = _wants_show_all_previous(message)

        wants_prep = _wants_meeting_prep(message)

        wants_new = (
            choice in {"1", "yes", "y", "ok", "okay", "sure"}
            or _wants_new_interaction(message)
        )

        if wants_edit:
            # NOTE: re-opening a saved interaction for editing needs a
            # tool to fetch it back into a draft by id — same
            # get_interaction dependency as "view", but this time we
            # also need to know how updates get written back (does
            # save_interaction support update-by-id, or only insert?).
            # Placeholder until that's confirmed.
            state["assistant_message"] = (
                "Editing a saved interaction isn't wired up yet — I need "
                "to know whether your save_interaction tool supports "
                "updating an existing record by id, or only inserting new "
                "ones. Let me know and I'll build this properly."
            )
            state["awaiting_post_save_choice"] = True
            return state

        if wants_show_all:
            # NOTE: listing multiple past interactions needs a
            # list/query tool against the DB (e.g. by HCP or by user)
            # that doesn't exist in the files shared so far.
            state["assistant_message"] = (
                "I can only recall the single most recent interaction from "
                "this session right now — showing a full history needs a "
                "list/search tool against the database that isn't built "
                "yet. Want me to help design that next?"
            )
            state["awaiting_post_save_choice"] = True
            return state

        if wants_prep:
            # NOTE: this is a new feature — needs a definition of what
            # "prep" means (talking points from past interactions?
            # open follow-ups? outstanding requests from the doctor?)
            # and a way to fetch that doctor's interaction history.
            state["assistant_message"] = (
                "I'd love to build meeting prep, but I want to get it right — "
                "should it summarize open follow-ups with this doctor, "
                "pull their past interaction history, or something else? "
                "Let me know what would actually be useful here."
            )
            state["awaiting_post_save_choice"] = True
            return state

        if wants_preview:

            last_id = state.get("last_interaction_id")

            if not last_id:
                state["assistant_message"] = (
                    "I don't have a previously saved interaction to show you."
                )
                return state

            try:
                from app.tools.get_interaction import get_interaction

                saved_draft = get_interaction(db=db, interaction_id=last_id)

            except ImportError:
                # get_interaction doesn't exist yet — fail gracefully
                # instead of crashing the whole request.
                state["assistant_message"] = (
                    "Viewing a saved interaction isn't fully wired up on "
                    "the backend yet. Would you like to log another "
                    "interaction instead?"
                )
                state["awaiting_post_save_choice"] = True
                return state

            except Exception:
                # get_interaction exists but failed (e.g. the HCP model
                # import/fields it assumes don't match the real schema).
                # Fail gracefully rather than crashing the request.
                state["assistant_message"] = (
                    "I ran into an issue fetching that saved interaction. "
                    "Would you like to log another interaction instead?"
                )
                state["awaiting_post_save_choice"] = True
                return state

            state["assistant_message"] = (
                build_review(draft=saved_draft)
                + "\n\nWould you like to log another interaction?"
            )
            # Stay in "post-save choice" mode in case they now say "yes"
            state["awaiting_post_save_choice"] = True

            return state

        if wants_new or choice in {"", "1"}:
            state.update(
                {
                    "draft": {},
                    "highlighted_fields": [],
                    "assistant_message": "Sure — who is the Healthcare Professional this interaction is with?",
                    "ready_for_confirmation": False,
                    "confirmed": False,
                }
            )
            return state

        # Anything else (e.g. "no") — acknowledge and stop prompting.
        state["assistant_message"] = (
            "Okay, let me know whenever you'd like to log a new interaction."
        )
        return state

    # ---------------------------------------------
    # Intent: user wants to view a previously saved
    # interaction (does not touch the current draft)
    # ---------------------------------------------

    if _wants_previous_review(message):

        last_id = state.get("last_interaction_id")

        if not last_id:
            state["assistant_message"] = (
                "I don't have a previously saved interaction in this "
                "session to show you yet."
            )
            return state

        try:
            from app.tools.get_interaction import get_interaction

            saved_draft = get_interaction(db=db, interaction_id=last_id)

        except ImportError:
            state["assistant_message"] = (
                "Viewing a saved interaction isn't fully wired up on "
                "the backend yet."
            )
            return state

        except Exception:
            state["assistant_message"] = (
                "I ran into an issue fetching that saved interaction."
            )
            return state

        state["assistant_message"] = build_review(draft=saved_draft)

        return state

    # ---------------------------------------------
    # Intent: user explicitly wants to start logging
    # a new interaction (in case they say this instead
    # of just replying "yes" to the post-save prompt)
    # ---------------------------------------------

    if _wants_new_interaction(message) and not draft:
        # Draft is already empty (e.g. right after a save) — just ask
        # the first question instead of running extraction on this
        # intent-only message.
        state.update(
            {
                "draft": {},
                "highlighted_fields": [],
                "assistant_message": "Sure — who is the Healthcare Professional this interaction is with?",
                "ready_for_confirmation": False,
                "confirmed": False,
            }
        )
        return state

    if _wants_new_interaction(message) and draft:
        # User wants to abandon whatever's in progress and start fresh.
        state.update(
            {
                "draft": {},
                "highlighted_fields": [],
                "assistant_message": "Okay, starting a new interaction. Who is the Healthcare Professional this interaction is with?",
                "ready_for_confirmation": False,
                "confirmed": False,
            }
        )
        return state

    # ---------------------------------------------
    # Extract structured information
    # ---------------------------------------------

    extracted = extract_interaction(message)

    merge_result = update_draft(
        current_draft=draft,
        updates=extracted,
    )

    draft = merge_result["draft"]

    highlighted = merge_result["highlighted_fields"]

    # ------------------------------------------------------
    # Resolve pending HCP selection
    # ------------------------------------------------------

    if (
        draft.get("hcp_search_result")
        and draft["hcp_search_result"]["count"] > 1
        and "hcp_id" not in draft
    ):

        choice = message.lower().strip()

        hcps = draft["hcp_search_result"]["hcps"]

        selected = None

        # User entered a number or ordinal word
        ordinal_map = {
            "first": 1,
            "second": 2,
            "third": 3,
            "fourth": 4,
            "fifth": 5,
        }

        if choice in ordinal_map:
            choice = str(ordinal_map[choice])

        if choice.isdigit():

            index = int(choice) - 1

            if 0 <= index < len(hcps):
                selected = hcps[index]

        else:

            # Match by doctor name or organization
            for hcp in hcps:

                if (
                    choice in hcp["name"].lower()
                    or choice in hcp["organization"].lower()
                ):
                    selected = hcp
                    break

        if selected:

            draft["hcp_id"] = selected["id"]

            # Selection completed
            draft.pop("hcp_search_result", None)

        else:

            state["draft"] = draft
            state["highlighted_fields"] = highlighted
            state["assistant_message"] = (
                "I couldn't identify the Healthcare Professional.\n\n"
                "Please reply with the doctor's number, name, or organization."
            )

            return state

    # ---------------------------------------------
    # Search HCP
    # ---------------------------------------------

    if draft.get("hcp_name"):

        search_result = search_hcp(
            db=db,
            doctor_name=draft["hcp_name"],
        )

        draft["hcp_search_result"] = search_result  # type: ignore

        if not search_result["found"]:  # type: ignore

            pending = {
                "full_name": draft["hcp_name"],
                "organization": draft.get("hcp_organization") or "",
                "specialty": draft.get("hcp_specialty") or None,
                "city": draft.get("hcp_city") or None,
            }

            still_missing = [
                field for field in ("specialty", "city")
                if not pending.get(field)
            ]

            if not still_missing:
                # Everything needed was already in the original message —
                # create the HCP immediately, no need to ask anything.
                from app.tools.create_hcp import create_hcp

                try:
                    new_hcp = create_hcp(
                        db=db,
                        full_name=pending["full_name"],
                        specialty=pending["specialty"],
                        organization=pending["organization"],
                        city=pending["city"],
                    )
                except Exception:
                    state["draft"] = draft
                    state["highlighted_fields"] = highlighted
                    state["assistant_message"] = (
                        f"I couldn't find {draft['hcp_name']}, and ran "
                        "into an issue creating them as a new HCP. Could "
                        "you try again?"
                    )
                    return state

                draft["hcp_id"] = new_hcp["id"]
                draft["hcp_specialty"] = pending["specialty"]
                draft["hcp_city"] = pending["city"]
                draft.pop("hcp_search_result", None)
                draft.pop("hcp_organization", None)

                # Continue straight into the required-fields check with
                # everything already extracted from the original message —
                # no interruption, matching the requested behavior.
                return _check_required_fields_and_respond(
                    state, draft, highlighted
                )

            # Something's genuinely missing — ask only for that, and
            # only that, framed naturally rather than a fixed template.
            state["pending_new_hcp"] = pending
            state["awaiting_new_hcp_details"] = True

            # CRITICAL: persist the draft extracted from the original
            # message (hcp_name, subject, notes, sentiment, everything)
            # before returning. This app is fully stateless server-side —
            # whatever isn't written into state here is gone on the next
            # turn, since the frontend only sends back what it was given.
            state["draft"] = draft
            state["highlighted_fields"] = highlighted

            known_bits = [f"Name: {pending['full_name']}"]

            if pending["organization"]:
                known_bits.append(f"Hospital: {pending['organization']}")

            if pending.get("specialty"):
                known_bits.append(f"Specialty: {pending['specialty']}")

            if pending.get("city"):
                known_bits.append(f"City: {pending['city']}")

            missing_phrase = " and ".join(still_missing)

            state["assistant_message"] = (
                f"I couldn't find {draft['hcp_name']} — I'll add them as "
                f"a new HCP ({', '.join(known_bits)}). "
                f"I just need the {missing_phrase} to finish that — "
                "could you let me know?"
            )

            return state

        if search_result["count"] == 1:  # type: ignore

            hcp = search_result["hcps"][0]  # type: ignore

            draft["hcp_id"] = hcp["id"]  # type: ignore

        elif search_result["count"] > 1:  # type: ignore

            prompt_message = (
                f'I found multiple Healthcare Professionals matching '
                f'"{draft["hcp_name"]}":\n\n'
            )

            for index, hcp in enumerate(
                search_result["hcps"],  # type: ignore
                start=1,
            ):
                prompt_message += (
                    f"{index}. "
                    f"{hcp['name']} "
                    f"({hcp['organization']})\n"
                )

            prompt_message += (
                "\nPlease reply with:\n"
                "• the number\n"
                "• the doctor's name\n"
                "• or the organization."
            )

            state["draft"] = draft
            state["highlighted_fields"] = highlighted
            state["assistant_message"] = prompt_message  # type: ignore

            return state

    # ---------------------------------------------
    # Required fields
    # ---------------------------------------------

    return _check_required_fields_and_respond(state, draft, highlighted)


def _check_required_fields_and_respond(
    state: dict,
    draft: dict,
    highlighted: list,
) -> dict:
    """
    Shared tail logic: check required fields, ask the next question if
    something's missing, or finalize and build the review if complete.
    Used both by the normal conversation flow and by the new-HCP-creation
    branch, so a fresh HCP creation can proceed straight to the next
    question/review without re-running interaction extraction.
    """

    required_fields = [
        "hcp_name",
        "interaction_type",
        "interaction_date",
        "subject",
        "notes",
    ]

    missing = []

    for field in required_fields:

        value = draft.get(field)

        if value is None:
            missing.append(field)

        elif isinstance(value, str):

            if value.strip() == "":
                missing.append(field)

    # ---------------------------------------------
    # Need more information?
    # ---------------------------------------------

    if missing:

        next_field = missing[0]

        questions = {
            "interaction_type":
                "What type of interaction was it (Meeting, Call, Email, Conference etc.)?",

            "interaction_date":
                "When did the interaction happen?",

            "subject":
                "What was the main subject discussed?",

            "notes":
                "Could you briefly summarize the discussion?",
        }

        question = questions.get(
            next_field,
            f"Please provide {next_field}.",
        )

        state.update(
            {
                "draft": draft,
                "highlighted_fields": highlighted,
                "assistant_message": question,
                "ready_for_confirmation": False,
                "current_field": next_field,
            }
        )

        return state

    # ---------------------------------------------
    # Draft complete
    # ---------------------------------------------

    # Sentiment is optional and may genuinely never have been mentioned
    # across the whole conversation. Default it here, once, at
    # finalization time — NOT inside extract_interaction, where doing so
    # would clobber a correctly-set sentiment on every unrelated turn.
    if not draft.get("sentiment"):
        draft["sentiment"] = "neutral"

    # NOTE: no full field-by-field text dump here anymore. The draft
    # panel in the UI (bound to this same draft via Redux) is the
    # source of truth for reviewing the filled-in fields — the chat
    # message is just a short conversational prompt.
    state.update(
        {
            "draft": draft,
            "highlighted_fields": highlighted,
            "assistant_message": (
                "I've filled in the details on the form — take a look, "
                "and save it whenever you're ready, or tell me what to change."
            ),
            "ready_for_confirmation": True,
            "current_field": None,
        }
    )

    return state


# ==========================================================
# Review Node
# ==========================================================


def review_node(state: dict) -> dict:
    """
    Review node.

    Shows the generated review and waits for user confirmation.
    Also allows the user to correct fields before saving
    (e.g. "actually it was Dr. Mehta, not Dr. Verma").
    """

    # Defense in depth: if routing sends a post-save reply here instead
    # of conversation_node, don't treat it as a save confirmation or a
    # correction against a stale draft.
    if state.get("awaiting_post_save_choice"):
        state["confirmed"] = False
        state["assistant_message"] = (
            "Let's get that other interaction request sorted first — "
            "could you tell me again what you'd like to do "
            "(log another interaction, or preview the last one)?"
        )
        return state

    raw_message = state.get("message", "")
    message = raw_message.strip().lower()

    positive = {
        "yes",
        "y",
        "ok",
        "okay",
        "confirm",
        "save",
        "proceed",
    }

    if message in positive:
        state["confirmed"] = True
        return state

    negative_only = {
        "no",
        "n",
        "cancel",
        "stop",
    }

    draft = deepcopy(state.get("draft", {}))

    # A plain "no" isn't a correction to extract — just acknowledge and
    # ask what to change. Anything else is treated as a potential
    # correction (e.g. "change the date to yesterday",
    # "it was actually Dr. Mehta").
    if message not in negative_only:

        extracted = extract_interaction(raw_message)

        merge_result = update_draft(
            current_draft=draft,
            updates=extracted,
        )

        draft = merge_result["draft"]
        highlighted = merge_result["highlighted_fields"]

        state["draft"] = draft
        state["highlighted_fields"] = highlighted

        if highlighted:
            # Something actually changed — short, specific acknowledgment.
            # The full field values live in the draft panel, not the chat.
            changed_list = ", ".join(
                field.replace("_", " ") for field in highlighted
            )
            state["assistant_message"] = (
                f"Updated {changed_list}. Take a look at the form and "
                "save when you're ready, or let me know what else to change."
            )
        else:
            # Nothing recognizable changed — say so plainly rather than
            # silently repeating the same state.
            state["assistant_message"] = (
                "I didn't catch a change to apply there. What would you "
                "like to update, or type 'save' to log it as is?"
            )

        state["confirmed"] = False
        return state

    # Plain "no" — acknowledge and wait for what to change.
    state["assistant_message"] = (
        "No problem — what would you like to change?"
    )

    state["confirmed"] = False

    return state


# ==========================================================
# Save Node
# ==========================================================


def save_node(state: dict) -> dict:
    """
    Persist the interaction and reset the conversation state so the
    agent is ready to log a fresh interaction right away.

    Safety guard: regardless of how routing lands on this node, we
    NEVER persist a draft that's empty or missing required fields.
    This protects against routing bugs where a stray "Yes" (meant as
    an answer to "log another interaction?") gets reinterpreted as a
    save confirmation against a stale or cleared draft.
    """

    draft = state.get("draft") or {}

    required_fields = [
        "hcp_name",
        "interaction_type",
        "interaction_date",
        "subject",
        "notes",
    ]

    missing = [
        field for field in required_fields
        if not draft.get(field)
        or (isinstance(draft.get(field), str) and not draft[field].strip())
    ]

    if missing:
        # Refuse to save. This should not normally be reachable if
        # routing is correct, but it's cheap insurance against
        # duplicate/empty saves.
        state["saved"] = False
        state["confirmed"] = False
        state["ready_for_confirmation"] = False
        state["assistant_message"] = (
            "I don't have a complete interaction to save right now — "
            "looks like there's nothing pending. "
            "Would you like to log a new interaction?"
        )
        return state

    db = state["db"]

    result = save_interaction(
        db=db,
        draft=draft,
    )

    state["saved"] = True

    # Keep a reference to the just-saved interaction so the user can
    # ask to see it again later in the session.
    state["last_interaction_id"] = result["interaction_id"]

    # NOTE: intentionally NOT clearing draft/highlighted_fields here.
    # The UI should keep showing the just-saved interaction until the
    # user explicitly asks to log another one — that's handled in
    # conversation_node's "awaiting_post_save_choice" branch below,
    # which is the only place that should clear the draft.
    state["current_field"] = None
    state["ready_for_confirmation"] = False
    state["confirmed"] = False

    # Track that the next message should be interpreted as an answer
    # to the post-save menu rather than a save confirmation or
    # free-text extraction target.
    state["awaiting_post_save_choice"] = True

    state["assistant_message"] = (
        "Interaction logged successfully. ✅\n\n"
        f"I've logged your interaction with {draft.get('hcp_name', 'the doctor')}.\n\n"
        "What would you like to do next?\n"
        "1. Log another interaction\n"
        "2. View this interaction\n"
        "\nReply with a number, or just tell me what you'd like."
    )

    return state