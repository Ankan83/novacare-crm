import { useEffect, useRef, useState } from "react";
import { shallowEqual, useDispatch, useSelector } from "react-redux";

import { sendChat } from "../api";

import {
  addMessage,
  setLoading,
  setChatting,
  setError,
  replaceDraft,
  setHighlightedFields,
  setConversationStage,
  setReadyForConfirmation,
  setSaved,
  setCurrentField,
  setLastInteractionId,
  setAwaitingPostSaveChoice,
  setAwaitingNewHcpDetails,
  setPendingNewHcp,
  showToast,
} from "../store";

const buildHistory = (history) =>
  history.map((message) => ({
    role: message.role,
    content: message.content,
  }));

export default function useChat() {
  const dispatch = useDispatch();

  const {
    chatting,
    messages,
    interactionDraft,
    conversationStage,
    readyForConfirmation,
    currentField,
    lastInteractionId,
    awaitingPostSaveChoice,
    awaitingNewHcpDetails,
    pendingNewHcp,
  } = useSelector(
    (state) => ({
      chatting: state.crm.chatting,
      messages: state.crm.messages,
      interactionDraft: state.crm.interactionDraft,
      conversationStage: state.crm.conversationStage,
      readyForConfirmation: state.crm.readyForConfirmation,
      currentField: state.crm.currentField,
      lastInteractionId: state.crm.lastInteractionId,
      awaitingPostSaveChoice: state.crm.awaitingPostSaveChoice,
      awaitingNewHcpDetails: state.crm.awaitingNewHcpDetails,
      pendingNewHcp: state.crm.pendingNewHcp,
    }),
    shallowEqual,
  );

  const [chatInput, setChatInput] = useState("");
  const [offline, setOffline] = useState(
    typeof navigator !== "undefined" && !navigator.onLine,
  );

  const chatEndRef = useRef(null);
  const sendMessageRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, chatting]);

  useEffect(() => {
    const savedInput = window.localStorage.getItem("nova-chat-draft");
    if (savedInput) setChatInput(savedInput);

    const handleOnline = async () => {
      setOffline(false);
      const queued = JSON.parse(
        window.localStorage.getItem("nova-offline-queue") || "[]",
      );
      window.localStorage.removeItem("nova-offline-queue");
      for (const item of queued) {
        const delivered = await sendMessageRef.current?.(item.text, true);
        if (!delivered) break;
      }
    };
    const handleOffline = () => setOffline(true);
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  async function sendMessage(customMessage = null, fromQueue = false) {
    const text = (customMessage ?? chatInput).trim();

    if (!text || chatting) return false;

    const userMessage = {
      role: "user",
      content: text,
    };

    dispatch(addMessage(userMessage));

    if (!customMessage) {
      setChatInput("");
      window.localStorage.removeItem("nova-chat-draft");
    }

    dispatch(setLoading(true));
    dispatch(setChatting(true));
    dispatch(setError(null));

    try {
      const response = await sendChat({
        message: text,
        history: buildHistory([...messages, userMessage]),
        draft: interactionDraft,
        conversation_stage: conversationStage,
        ready_for_confirmation: readyForConfirmation,
        // These three must round-trip every turn, or the backend loses
        // track of what field it's waiting on, which interaction was
        // last saved, and whether the user is mid-way through the
        // post-save "log another / view / edit" menu.
        current_field: currentField ?? null,
        last_interaction_id: lastInteractionId ?? null,
        awaiting_post_save_choice: awaitingPostSaveChoice ?? false,
        awaiting_new_hcp_details: awaitingNewHcpDetails ?? false,
        pending_new_hcp: pendingNewHcp ?? null,
      });

      dispatch(
        addMessage({
          role: "assistant",
          content: response.assistant_message,
        }),
      );

      // Always dispatch, even when draft is {} — an empty draft is a
      // real, meaningful value (e.g. right after a save) and must
      // fully REPLACE the old draft. The backend always sends the
      // complete draft, never a partial patch, so replaceDraft (not
      // updateDraft's merge) is the correct action here — a merge
      // would leave stale fields behind when the backend clears
      // the draft after a save.
      dispatch(replaceDraft(response.draft ?? {}));

      dispatch(setHighlightedFields(response.highlighted_fields ?? []));

      if (response.conversation_stage) {
        dispatch(setConversationStage(response.conversation_stage));
      }

      dispatch(
        setReadyForConfirmation(response.ready_for_confirmation ?? false),
      );

      dispatch(setSaved(response.saved ?? false));

      dispatch(setCurrentField(response.current_field ?? null));

      dispatch(setLastInteractionId(response.last_interaction_id ?? null));

      dispatch(
        setAwaitingPostSaveChoice(response.awaiting_post_save_choice ?? false),
      );

      dispatch(
        setAwaitingNewHcpDetails(response.awaiting_new_hcp_details ?? false),
      );

      dispatch(setPendingNewHcp(response.pending_new_hcp ?? null));

      if (response.saved) {
        dispatch(
          showToast({
            type: "success",
            title: "Interaction Saved",
            message: "The interaction has been saved successfully.",
          }),
        );
      }
      return true;
    } catch (err) {
      if (!navigator.onLine || err instanceof TypeError) {
        const queued = JSON.parse(
          window.localStorage.getItem("nova-offline-queue") || "[]",
        );
        if (!fromQueue) {
          queued.push({ text, queuedAt: new Date().toISOString() });
          window.localStorage.setItem(
            "nova-offline-queue",
            JSON.stringify(queued),
          );
        }
        dispatch(
          showToast({
            type: "warning",
            title: "Saved offline",
            message: "Your message will be sent automatically when you reconnect.",
          }),
        );
        return false;
      }
      dispatch(setError(err.message));

      dispatch(
        addMessage({
          role: "assistant",
          content: "Sorry, I couldn't process your request. Please try again.",
        }),
      );
      return false;

      dispatch(
        showToast({
          type: "error",
          title: "Request Failed",
          message: err.message ?? "Unable to reach the server.",
        }),
      );
    } finally {
      dispatch(setLoading(false));
      dispatch(setChatting(false));
    }
  }

  sendMessageRef.current = sendMessage;

  function onKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return {
    chatting,
    messages,

    chatInput,
    setChatInput,

    sendMessage,
    onKeyDown,

    chatEndRef,
    offline,
  };
}
