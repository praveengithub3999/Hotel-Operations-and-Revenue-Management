import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../services/api";

function Rooms() {
  const [rooms, setRooms] = useState([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);

  const loadRooms = useCallback(async () => {
    setLoading(true);

    try {
      const response = await api.get("/rooms/");

      setRooms(response.data);
      setMessage("");
    } catch (error) {
      console.error(error);
      setMessage("Unable to load rooms.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      void loadRooms();
    }, 0);

    return () => clearTimeout(timer);
  }, [loadRooms]);

  const getStatusColor = (status) => {
    const colors = {
      AVAILABLE: { background: "#d1fae5", color: "#065f46" },
      OCCUPIED: { background: "#dbeafe", color: "#1d4ed8" },
      RESERVED: { background: "#fef3c7", color: "#92400e" },
      DIRTY: { background: "#fee2e2", color: "#991b1b" },
      CLEANING: { background: "#ede9fe", color: "#5b21b6" },
      MAINTENANCE: { background: "#ffedd5", color: "#9a3412" },
      OUT_OF_SERVICE: { background: "#e5e7eb", color: "#374151" },
    };

    return colors[status] || {
      background: "#f1f5f9",
      color: "#334155",
    };
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
            Room Management
          </h1>
          <p
            style={{
              color: "#64748b",
              margin: 0,
              fontSize: "14px",
              lineHeight: "1.5",
            }}
          >
            View room availability and current status.
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <button onClick={loadRooms} style={buttonStyle} disabled={loading}>
            {loading ? "Loading..." : "Refresh"}
          </button>

          <Link to="/dashboard" style={linkStyle}>
            Dashboard
          </Link>
        </div>
      </div>

      {message && <p style={{ color: "#b91c1c" }}>{message}</p>}

      {loading ? (
        <p>Loading rooms...</p>
      ) : rooms.length === 0 ? (
        <div style={cardStyle}>
          <p>No rooms found.</p>
        </div>
      ) : (
        <>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))",
              gap: "18px",
              marginBottom: "28px",
            }}
          >
            {[
              "AVAILABLE",
              "OCCUPIED",
              "RESERVED",
              "DIRTY",
              "CLEANING",
              "MAINTENANCE",
            ].map((status) => (
              <div key={status} style={cardStyle}>
                <p
                  style={{
                    margin: "0 0 10px",
                    color: "#64748b",
                    fontSize: "14px",
                  }}
                >
                  {status.replaceAll("_", " ")} ROOMS
                </p>

                <h2 style={{ margin: 0, fontSize: "30px" }}>
                  {rooms.filter((room) => room.status === status).length}
                </h2>
              </div>
            ))}
          </div>

          <div style={cardStyle}>
            <h2 style={{ marginTop: 0 }}>All Rooms</h2>

            <div style={{ overflowX: "auto" }}>
              <table
                style={{
                  width: "100%",
                  borderCollapse: "collapse",
                  textAlign: "left",
                }}
              >
                <thead>
                  <tr style={{ background: "#f8fafc" }}>
                    <th style={cellStyle}>Room ID</th>
                    <th style={cellStyle}>Room Number</th>
                    <th style={cellStyle}>Floor</th>
                    <th style={cellStyle}>Room Type ID</th>
                    <th style={cellStyle}>Status</th>
                  </tr>
                </thead>

                <tbody>
                  {rooms.map((room) => (
                    <tr key={room.id}>
                      <td style={cellStyle}>{room.id}</td>
                      <td style={cellStyle}>
                        <strong>{room.room_number}</strong>
                      </td>
                      <td style={cellStyle}>{room.floor}</td>
                      <td style={cellStyle}>{room.room_type_id}</td>
                      <td style={cellStyle}>
                        <span
                          style={{
                            ...getStatusColor(room.status),
                            padding: "6px 10px",
                            borderRadius: "20px",
                            fontSize: "12px",
                            fontWeight: 600,
                            whiteSpace: "nowrap",
                          }}
                        >
                          {room.status.replaceAll("_", " ")}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

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
};

const buttonStyle = {
  background: "#0f766e",
  color: "#ffffff",
  border: "none",
  padding: "10px 18px",
  borderRadius: "8px",
  cursor: "pointer",
};

const linkStyle = {
  background: "#ffffff",
  color: "#0f766e",
  border: "1px solid #0f766e",
  padding: "10px 18px",
  borderRadius: "8px",
  textDecoration: "none",
};

export default Rooms;
