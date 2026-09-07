import "../../styles/ConfirmationCard.css";

export default function ConfirmationCard({ onConfirm, onEdit }) {
  return (
    <div className="confirmation-card">
      <h3>Review Complete</h3>

      <p>Please verify the interaction details.</p>

      <div className="confirmation-actions">
        <button className="confirm-btn" onClick={onConfirm}>
          ✓ Confirm & Save
        </button>

        <button className="edit-btn" onClick={onEdit}>
          Continue Editing
        </button>
      </div>
    </div>
  );
}
