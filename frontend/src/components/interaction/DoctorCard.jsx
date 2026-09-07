import "../../styles/DoctorCard.css";

export default function DoctorCard({ doctor = {}, selected = false, onClick }) {
  const initials = doctor.name
    ? doctor.name
        .split(" ")
        .map((word) => word[0])
        .join("")
        .substring(0, 2)
        .toUpperCase()
    : "DR";

  return (
    <div
      className={`doctor-card ${selected ? "selected" : ""}`}
      onClick={onClick}
    >
      <div className="doctor-avatar">{initials}</div>

      <div className="doctor-info">
        <h3>{doctor.name || "Healthcare Professional"}</h3>

        <p>{doctor.specialty || "Specialty not available"}</p>

        <div className="doctor-meta">
          <span>📍 {doctor.city || doctor.location || "Location"}</span>

          <span>
            🏥 {doctor.organization || doctor.hospital || "Organization"}
          </span>
        </div>
      </div>

      <div className="doctor-status">
        <span className={`status-dot ${selected ? "active" : ""}`} />

        <span>{selected ? "Selected" : "Available"}</span>
      </div>
    </div>
  );
}
