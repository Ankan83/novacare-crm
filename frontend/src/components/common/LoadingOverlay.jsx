import "../../styles/LoadingOverlay.css";

export default function LoadingOverlay({
  show,
  text = "Nova is analyzing your interaction...",
}) {
  if (!show) return null;

  return (
    <div className="loading-overlay">
      <div className="loading-card">
        <div className="loading-logo">N</div>

        <div className="loading-spinner">
          <span></span>
          <span></span>
          <span></span>
        </div>

        <h2>Nova AI</h2>

        <p>{text}</p>
      </div>
    </div>
  );
}
