import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

function Guests() {
  const [guests, setGuests] = useState([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);

  const navigate = useNavigate();

  const loadGuests = async () => {
    setLoading(true);

    try {
      const token = localStorage.getItem("token");

      const response = await api.get("/guests/", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setGuests(response.data);
      setMessage("");
    } catch (error) {
      console.error(error);

      if (error.response?.status === 401) {
        localStorage.removeItem("token");
        navigate("/", { replace: true });
        return;
      }

      setMessage("Unable to load guests. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGuests();
  }, []);

  const cardStyle = {
    background: "#ffffff",
    border: "1px solid #e5eaf1",
    borderRadius: "12px",
    padding: "22px",
    boxShadow: "0 3px 12px rgba(15, 23, 42, 0.035)",
  };

  const cellStyle = {
    padding: "14px 12px",
    borderBottom: "1px solid #e5eaf1",
    fontSize: "14px",
    textAlign: "left",
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#f4f7fb",
        padding: "32px",
        color: "#17243a",
        boxSizing: "border-box",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "15px",
          flexWrap: "wrap",
          marginBottom: "28px",
        }}
      >
        <div>
          <h1
            style={{
              margin: "0 0 8px",
              fontSize: "30px",
              lineHeight: "1.3",
              fontWeight: 700,
              color: "#17243a",
            }}
          >
            Guest Management
          </h1>

          <p
            style={{
              color: "#64748b",
              margin: 0,
              fontSize: "14px",
              lineHeight: "1.5",
            }}
          >
            View guest contact details and guest records.
          </p>
        </div>

        <button
          type="button"
          onClick={loadGuests}
          disabled={loading}
          style={{
            background: "#0f766e",
            color: "#ffffff",
            border: "none",
            padding: "11px 18px",
            borderRadius: "8px",
            cursor: "pointer",
          }}
        >
          {loading ? "Loading..." : "Refresh Guests"}
        </button>
      </div>

      {message && (
        <p style={{ color: "#b91c1c", marginBottom: "20px" }}>
          {message}
        </p>
      )}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "18px",
          marginBottom: "28px",
        }}
      >
        <div style={cardStyle}>
          <p style={{ color: "#64748b", margin: "0 0 10px" }}>
            TOTAL GUESTS
          </p>
          <h2 style={{ margin: 0, fontSize: "30px" }}>
            {guests.length}
          </h2>
        </div>

        <div style={cardStyle}>
          <p style={{ color: "#64748b", margin: "0 0 10px" }}>
            EMAIL RECORDS
          </p>
          <h2 style={{ margin: 0, fontSize: "30px" }}>
            {guests.filter((guest) => guest.email).length}
          </h2>
        </div>

        <div style={cardStyle}>
          <p style={{ color: "#64748b", margin: "0 0 10px" }}>
            PHONE RECORDS
          </p>
          <h2 style={{ margin: 0, fontSize: "30px" }}>
            {guests.filter((guest) => guest.phone).length}
          </h2>
        </div>
      </div>

      <div style={cardStyle}>
        <h2 style={{ margin: "0 0 20px", fontSize: "21px" }}>
          All Guests
        </h2>

        {loading ? (
          <p>Loading guest records...</p>
        ) : guests.length === 0 ? (
          <p>No guests found.</p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
              }}
            >
              <thead>
                <tr style={{ background: "#f8fafc" }}>
                  <th style={cellStyle}>Guest ID</th>
                  <th style={cellStyle}>Guest Name</th>
                  <th style={cellStyle}>Email</th>
                  <th style={cellStyle}>Phone</th>
                </tr>
              </thead>

              <tbody>
                {guests.map((guest) => (
                  <tr key={guest.id}>
                    <td style={cellStyle}>{guest.id}</td>

                    <td style={cellStyle}>
                      <strong>
                        {guest.first_name} {guest.last_name}
                      </strong>
                    </td>

                    <td style={cellStyle}>
                      {guest.email || "Not provided"}
                    </td>

                    <td style={cellStyle}>
                      {guest.phone || "Not provided"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default Guests;