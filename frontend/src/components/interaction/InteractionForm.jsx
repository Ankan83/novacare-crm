import { useMemo } from "react";
import { useSelector } from "react-redux";

import "../../styles/InteractionForm.css";

const GENERAL_FIELDS = [
  {
    key: "hcp_name",
    label: "Healthcare Professional",
    icon: "👨‍⚕️",
  },
  {
    key: "hcp_specialty",
    label: "Specialty",
    icon: "🩺",
  },
  {
    key: "hcp_city",
    label: "City",
    icon: "📍",
  },
  {
    key: "interaction_type",
    label: "Interaction Type",
    icon: "🤝",
  },
  {
    key: "interaction_date",
    label: "Interaction Date",
    icon: "📅",
  },
  {
    key: "duration_minutes",
    label: "Duration",
    icon: "⏱",
    formatter: (v) => (v ? `${v} Minutes` : null),
  },
];

const DISCUSSION_FIELDS = [
  {
    key: "subject",
    label: "Subject",
    icon: "📝",
  },
  {
    key: "notes",
    label: "Notes",
    icon: "📄",
  },
];

const INSIGHT_FIELDS = [
  {
    key: "topics",
    label: "Topics",
    icon: "🏷️",
    chips: true,
  },
  {
    key: "attendees",
    label: "Attendees",
    icon: "👥",
    chips: true,
  },
  {
    key: "sentiment",
    label: "Sentiment",
    icon: "😊",
  },
  {
    key: "follow_up",
    label: "Follow Up",
    icon: "🔄",
  },
];

function EmptyValue() {
  return <div className="empty-value">Waiting for Nova...</div>;
}

function ChipList({ values }) {
  if (!values || values.length === 0) {
    return <EmptyValue />;
  }

  return (
    <div className="chip-list">
      {values.map((item, index) => (
        <span key={`${item}-${index}`} className="chip">
          {item}
        </span>
      ))}
    </div>
  );
}

function FieldCard({ field, value, updated }) {
  const displayValue = useMemo(() => {
    if (field.formatter) {
      return field.formatter(value);
    }

    return value;
  }, [field, value]);

  return (
    <div className={`field-card ${updated ? "updated" : ""}`}>
      <div className="field-header">
        <span className="field-icon">{field.icon}</span>

        <span className="field-label">{field.label}</span>

        {updated && <span className="updated-badge">Updated</span>}
      </div>

      {field.chips ? (
        <ChipList values={displayValue} />
      ) : displayValue ? (
        <div className="field-content">{displayValue}</div>
      ) : (
        <EmptyValue />
      )}
    </div>
  );
}

function Section({ title, fields, draft, highlights }) {
  return (
    <section className="review-section">
      <h3>{title}</h3>

      <div className="review-grid">
        {fields.map((field) => (
          <FieldCard
            key={field.key}
            field={field}
            value={draft[field.key]}
            updated={highlights.includes(field.key)}
          />
        ))}
      </div>
    </section>
  );
}

export default function InteractionForm() {
  const { interactionDraft, highlightedFields } = useSelector(
    (state) => state.crm,
  );

  return (
    <div className="interaction-review">
      <div className="interaction-title">
        <h2>Interaction Details</h2>

        <p>Automatically extracted and structured by Nova AI.</p>
      </div>

      <Section
        title="General Information"
        fields={GENERAL_FIELDS}
        draft={interactionDraft}
        highlights={highlightedFields}
      />

      <Section
        title="Discussion"
        fields={DISCUSSION_FIELDS}
        draft={interactionDraft}
        highlights={highlightedFields}
      />

      <Section
        title="Insights"
        fields={INSIGHT_FIELDS}
        draft={interactionDraft}
        highlights={highlightedFields}
      />
    </div>
  );
}
