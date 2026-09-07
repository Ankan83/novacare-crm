import "../../styles/DoctorSelection.css";

export default function DoctorSelection({ doctors, onSelect }) {
  return (
    <div className="doctor-selection">
      <div className="doctor-selection-title">
        Select the correct Healthcare Professional
      </div>

      <div className="doctor-selection-list">
        {doctors.map((doctor, index) => (
          <div key={doctor.id ?? index} className="doctor-card-option">
            <div className="doctor-left">
              <div className="doctor-avatar">{doctor.name.charAt(0)}</div>

              <div>
                <h4>{doctor.name}</h4>

                <p>{doctor.organization}</p>
              </div>
            </div>

            <button
              className="doctor-select-btn"
              onClick={() => onSelect(index + 1)}
            >
              Select
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
