import "../../styles/Toast.css";

export default function Toast({ show, type = "info", title, message }) {
  if (!show) return null;

  return (
    <div className={`toast ${type}`}>
      <div className="toast-icon">
        {type === "success" && "✓"}
        {type === "error" && "✕"}
        {type === "warning" && "!"}
        {type === "info" && "i"}
      </div>

      <div className="toast-content">
        <h4>{title}</h4>

        <p>{message}</p>
      </div>
    </div>
  );
}
