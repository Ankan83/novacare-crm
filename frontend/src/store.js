import { configureStore, createSlice } from "@reduxjs/toolkit";

const initialDraft = {
  hcp_id: null,
  interaction_type: "",
  subject: "",
  notes: "",
  interaction_date: "",
  duration_minutes: 0,
  attendees: [],
  topics: [],
  summary: "",
  sentiment: "neutral",
  sentiment_reason: "",
  follow_up: "",
  hcp_search_result: null,
};

const initialToast = {
  open: false,
  type: "success",
  title: "",
  message: "",
};

const initialState = {
  // App state
  loading: false,
  chatting: false,
  error: null,

  // Chat
  messages: [],

  // CRM
  interactionDraft: initialDraft,
  highlightedFields: [],
  conversationStage: "conversation",
  selectedHcp: null,
  review: null,

  // Backend state
  readyForConfirmation: false,
  saved: false,

  // Which field the backend is currently waiting for an answer to.
  currentField: null,

  // Id of the most recently saved interaction this session, so
  // "view/edit this interaction" keeps working across turns.
  lastInteractionId: null,

  // True while the user is being asked the post-save menu
  // (log another / view / edit / show previous / prepare for meeting).
  awaitingPostSaveChoice: false,

  // True while the user has been offered to create a new HCP record
  // and is being asked for specialty/city.
  awaitingNewHcpDetails: false,

  // Partial HCP details collected so far (name, organization) while
  // awaitingNewHcpDetails is true.
  pendingNewHcp: null,

  // UI
  toast: initialToast,
};

const crmSlice = createSlice({
  name: "crm",
  initialState,

  reducers: {
    setLoading(state, action) {
      state.loading = action.payload;
    },

    setChatting(state, action) {
      state.chatting = action.payload;
    },

    setError(state, action) {
      state.error = action.payload;
    },

    addMessage(state, action) {
      state.messages.push(action.payload);
    },

    setMessages(state, action) {
      state.messages = action.payload;
    },

    clearMessages(state) {
      state.messages = [];
    },

    // NOTE: this is a MERGE, kept for any existing call sites that
    // intentionally patch a few fields. The backend always returns
    // the full, authoritative draft on every turn (never a partial
    // patch), so useChat.js should dispatch replaceDraft, not this,
    // when handling a /chat response — otherwise an empty draft after
    // "log another interaction" gets merged into (and erased by) the
    // stale existing draft instead of clearing it.
    updateDraft(state, action) {
      state.interactionDraft = {
        ...state.interactionDraft,
        ...action.payload,
      };
    },

    replaceDraft(state, action) {
      state.interactionDraft = action.payload;
    },

    clearDraft(state) {
      state.interactionDraft = {
        ...initialDraft,
      };
    },

    setHighlightedFields(state, action) {
      state.highlightedFields = action.payload || [];
    },

    clearHighlightedFields(state) {
      state.highlightedFields = [];
    },

    setConversationStage(state, action) {
      state.conversationStage = action.payload;
    },

    setSelectedHcp(state, action) {
      state.selectedHcp = action.payload;
    },

    setReview(state, action) {
      state.review = action.payload;
    },

    setReadyForConfirmation(state, action) {
      state.readyForConfirmation = action.payload;
    },

    setSaved(state, action) {
      state.saved = action.payload;
    },

    setCurrentField(state, action) {
      state.currentField = action.payload ?? null;
    },

    setLastInteractionId(state, action) {
      state.lastInteractionId = action.payload ?? null;
    },

    setAwaitingPostSaveChoice(state, action) {
      state.awaitingPostSaveChoice = action.payload ?? false;
    },

    setAwaitingNewHcpDetails(state, action) {
      state.awaitingNewHcpDetails = action.payload ?? false;
    },

    setPendingNewHcp(state, action) {
      state.pendingNewHcp = action.payload ?? null;
    },

    showToast(state, action) {
      state.toast = {
        open: true,
        ...action.payload,
      };
    },

    hideToast(state) {
      state.toast = {
        ...initialToast,
      };
    },

    resetConversation(state) {
      state.loading = false;
      state.chatting = false;
      state.error = null;

      state.messages = [];

      state.interactionDraft = {
        ...initialDraft,
      };

      state.highlightedFields = [];

      state.conversationStage = "conversation";

      state.selectedHcp = null;

      state.review = null;

      state.readyForConfirmation = false;

      state.saved = false;

      state.currentField = null;

      state.awaitingPostSaveChoice = false;

      state.awaitingNewHcpDetails = false;

      state.pendingNewHcp = null;

      // lastInteractionId intentionally NOT reset here — a fresh
      // conversation can still reference the last saved interaction
      // from this session (e.g. "view this interaction").
    },

    resetAll(state) {
      Object.assign(state, {
        ...initialState,
        interactionDraft: {
          ...initialDraft,
        },
        toast: {
          ...initialToast,
        },
      });
    },
  },
});

export const {
  setLoading,
  setChatting,
  setError,

  addMessage,
  setMessages,
  clearMessages,

  updateDraft,
  replaceDraft,
  clearDraft,

  setHighlightedFields,
  clearHighlightedFields,

  setConversationStage,
  setSelectedHcp,
  setReview,

  setReadyForConfirmation,
  setSaved,

  setCurrentField,
  setLastInteractionId,
  setAwaitingPostSaveChoice,
  setAwaitingNewHcpDetails,
  setPendingNewHcp,

  showToast,
  hideToast,

  resetConversation,
  resetAll,
} = crmSlice.actions;

const store = configureStore({
  reducer: {
    crm: crmSlice.reducer,
  },
});

export default store;
