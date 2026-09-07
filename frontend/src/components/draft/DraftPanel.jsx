import { useMemo } from "react";
import { useSelector } from "react-redux";

import "../../styles/DraftPanel.css";

const REQUIRED_FIELDS = [
  "hcp_name",
  "interaction_type",
  "interaction_date",
  "subject",
  "notes",
];

function hasValue(value) {
  if (value === null || value === undefined) return false;

  if (Array.isArray(value)) return value.length > 0;

  if (typeof value === "string") return value.trim().length > 0;

  return true;
}

export default function DraftPanel() {
  const {
    interactionDraft,
    readyForConfirmation,
    saved,
    highlightedFields,
    selectedHcp,
  } = useSelector((state) => state.crm);

  const progress = useMemo(() => {
    let completed = 0;

    REQUIRED_FIELDS.forEach((field) => {
      if (hasValue(interactionDraft[field])) {
        completed++;
      }
    });

    return Math.round((completed / REQUIRED_FIELDS.length) * 100);
  }, [interactionDraft]);

  const recentUpdates = highlightedFields.slice(0, 5);

  return (
    <section className="draft-dashboard">
      <div className="dashboard-header">
        <div>
          <h2>Interaction Review</h2>
          <p>AI extraction status</p>
        </div>

        {saved ? (
          <div className="status-pill saved">Saved</div>
        ) : readyForConfirmation ? (
          <div className="status-pill ready">Ready</div>
        ) : (
          <div className="status-pill collecting">Collecting</div>
        )}
      </div>

      <div className="progress-card">
        <div className="progress-top">
          <span>Completion</span>
          <strong>{progress}%</strong>
        </div>

        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{
              width: `${progress}%`,
            }}
          />
        </div>
      </div>

      <div className="summary-grid">
        <div className="summary-card">
          <span className="summary-label">Selected HCP</span>

          <strong>
            {selectedHcp || interactionDraft.hcp_name || "Waiting..."}
          </strong>
        </div>

        <div className="summary-card">
          <span className="summary-label">Interaction Type</span>

          <strong>{interactionDraft.interaction_type || "Waiting..."}</strong>
        </div>

        <div className="summary-card">
          <span className="summary-label">Date</span>

          <strong>{interactionDraft.interaction_date || "Waiting..."}</strong>
        </div>

        <div className="summary-card">
          <span className="summary-label">Sentiment</span>

          <strong>{interactionDraft.sentiment || "Waiting..."}</strong>
        </div>
      </div>

      <div className="updates-card">
        <h3>Recent AI Updates</h3>

        {recentUpdates.length === 0 ? (
          <p className="empty-text">
            {saved
              ? "Interaction saved. New AI updates will appear here."
              : "Nova is waiting for your first message."}
          </p>
        ) : (
          <ul>
            {recentUpdates.map((field) => (
              <li key={field}>✓ {field.replaceAll("_", " ")}</li>
            ))}
          </ul>
        )}
      </div>

      {readyForConfirmation && !saved && (
        <div className="review-banner">
          <div className="review-icon">✓</div>

          <div>
            <h4>Ready to Save</h4>

            <p>
              Nova has extracted the interaction. Review the details below and
              click
              <strong> Confirm & Save</strong>.
            </p>
          </div>
        </div>
      )}

      {saved && (
        <div className="success-banner">
          <div className="review-icon">🎉</div>

          <div>
            <h4>Interaction Saved</h4>

            <p>The interaction has been stored successfully.</p>
          </div>
        </div>
      )}
    </section>
  );
}
