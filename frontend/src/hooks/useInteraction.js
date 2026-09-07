import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import { fetchHcps, saveInteraction } from "../store";

const initialForm = {
  hcp_id: "",
  hcp_name: "",

  interaction_type: "Meeting",

  interaction_date: new Date().toISOString().slice(0, 10),

  interaction_time: new Date().toTimeString().slice(0, 5),

  duration_minutes: 30,

  attendees: "",

  topics: "",

  subject: "",

  notes: "",

  materials: "",

  samples: "",

  summary: "",

  sentiment: "",

  sentiment_reason: "",

  outcomes: "",

  follow_up: "",
};

export default function useInteraction() {
  const dispatch = useDispatch();

  const { hcps, saving, interactionDraft } = useSelector((state) => state.crm);

  const [form, setForm] = useState(initialForm);

  const [highlightedFields, setHighlightedFields] = useState([]);

  useEffect(() => {
    dispatch(fetchHcps());
  }, [dispatch]);

  useEffect(() => {
    if (!interactionDraft) return;

    const updatedFields = [];

    Object.entries(interactionDraft).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== "") {
        updatedFields.push(key);
      }
    });

    setHighlightedFields(updatedFields);

    const timer = setTimeout(() => {
      setHighlightedFields([]);
    }, 1200);

    setForm((current) => ({
      ...current,

      hcp_id:
        interactionDraft.hcp_id != null
          ? String(interactionDraft.hcp_id)
          : current.hcp_id,

      hcp_name: interactionDraft.hcp_name ?? current.hcp_name,

      interaction_type:
        interactionDraft.interaction_type ?? current.interaction_type,

      interaction_date: interactionDraft.interaction_date
        ? interactionDraft.interaction_date.slice(0, 10)
        : current.interaction_date,

      duration_minutes:
        interactionDraft.duration_minutes ?? current.duration_minutes,
      attendees: Array.isArray(interactionDraft.attendees)
        ? interactionDraft.attendees.join(", ")
        : current.attendees,

      topics: Array.isArray(interactionDraft.topics)
        ? interactionDraft.topics.join(", ")
        : current.topics,

      subject: interactionDraft.subject ?? current.subject,

      notes: interactionDraft.notes ?? current.notes,

      summary: interactionDraft.summary ?? current.summary,

      sentiment: interactionDraft.sentiment ?? current.sentiment,

      sentiment_reason:
        interactionDraft.sentiment_reason ?? current.sentiment_reason,

      follow_up: interactionDraft.follow_up ?? current.follow_up,
    }));

    return () => clearTimeout(timer);
  }, [interactionDraft]);

  useEffect(() => {
    if (!interactionDraft?.hcp_name) return;

    const hcp = hcps.find(
      (item) =>
        item.full_name.toLowerCase() ===
        interactionDraft.hcp_name.toLowerCase(),
    );

    if (!hcp) return;

    setForm((current) => ({
      ...current,
      hcp_id: String(hcp.id),
    }));
  }, [interactionDraft, hcps]);

  const change = (event) => {
    const { name, value } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));
  };

  const resetForm = () => {
    setForm({
      ...initialForm,
      interaction_date: new Date().toISOString().slice(0, 10),

      interaction_time: new Date().toTimeString().slice(0, 5),
    });
  };

  const submitInteraction = async () => {
    try {
      await dispatch(
        saveInteraction({
          hcp_id: Number(form.hcp_id),

          interaction_type: form.interaction_type,

          interaction_date: `${form.interaction_date}T${form.interaction_time}`,

          duration_minutes: Number(form.duration_minutes),

          subject: form.subject,

          notes: form.notes,

          attendees: form.attendees
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean),

          topics: form.topics
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean),

          summary: form.summary,

          sentiment: form.sentiment,

          sentiment_reason: form.sentiment_reason,

          follow_up: form.follow_up,
        }),
      ).unwrap();
      resetForm();

      return true;
    } catch (err) {
      console.error(err);
      return false;
    }
  };

  const isHighlighted = (field) => highlightedFields.includes(field);

  return {
    form,
    setForm,

    hcps,

    saving,

    change,

    submitInteraction,

    resetForm,

    isHighlighted,

    highlightedFields,
  };
}