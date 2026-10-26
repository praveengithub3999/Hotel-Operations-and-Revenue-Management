import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../services/api";

function Rooms() {
  const [rooms, setRooms] = useState([]);
  const [hotels, setHotels] = useState([]);
  const [roomTypes, setRoomTypes] = useState([]);
  const [message, setMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

  const [newRoom, setNewRoom] = useState({
    hotel_id: "",
    room_type_id: "",
    room_number: "",
    floor: "1",
  });

  // Extract user role from JWT token
  const token = localStorage.getItem("token");
  let role = "";
  try {
    if (token) {
      const payload = JSON.parse(
        atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/"))
      );
      role = payload.role || "";
    }
  } catch {
    role = "";
  }

  const canCreateRoom = role === "ADMIN";

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

  const loadMetadata = useCallback(async () => {
    try {
      const [hotelsRes, typesRes] = await Promise.all([
        api.get("/hotels/").catch(() => ({ data: [] })),
        api.get("/room-types/").catch(() => ({ data: [] })),
      ]);

      setHotels(hotelsRes.data || []);
      setRoomTypes(typesRes.data || []);

      if (hotelsRes.data?.length > 0) {
        setNewRoom((prev) => ({
          ...prev,
          hotel_id: prev.hotel_id || hotelsRes.data[0].id,
        }));
      }

      if (typesRes.data?.length > 0) {
        setNewRoom((prev) => ({
          ...prev,
          room_type_id: prev.room_type_id || typesRes.data[0].id,
        }));
      }
    } catch (err) {
      console.error("Failed to load hotels/room types:", err);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      void loadRooms();
      void loadMetadata();
    }, 0);

    return () => clearTimeout(timer);
  }, [loadRooms, loadMetadata]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNewRoom((prev) => ({ ...prev, [name]: value }));
  };

  const handleCreateRoom = async (e) => {
    e.preventDefault();
    setFormError("");
    setSuccessMessage("");

    if (!newRoom.room_number.trim()) {
      setFormError("Room number is required.");
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        hotel_id: parseInt(newRoom.hotel_id, 10),
        room_type_id: parseInt(newRoom.room_type_id, 10),
        room_number: newRoom.room_number.trim(),
        floor: parseInt(newRoom.floor, 10) || 1,
      };

      await api.post("/rooms/", payload);

      setSuccessMessage(`Room ${payload.room_number} created successfully!`);
      setShowCreateModal(false);
      setNewRoom({
        hotel_id: hotels[0]?.id || "",
        room_type_id: roomTypes[0]?.id || "",
        room_number: "",
        floor: "1",
      });

      await loadRooms();
    } catch (err) {
      console.error(err);
      let errorMsg = "Failed to create room. Please check input.";
      if (typeof err.response?.data?.detail === "string") {
        errorMsg = err.response.data.detail;
      } else if (Array.isArray(err.response?.data?.detail)) {
        errorMsg = err.response.data.detail
          .map((d) => `${d.loc ? d.loc.slice(-1)[0] + ': ' : ''}${d.msg}`)
          .join("; ");
      } else if (typeof err.response?.data === "string") {
        errorMsg = err.response.data;
      } else if (err.response?.data?.message) {
        errorMsg = err.response.data.message;
      } else if (err.message) {
        errorMsg = err.message;
      }
      setFormError(errorMsg);
    } finally {
      setSubmitting(false);
    }
  };

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
            View room availability, create new rooms, and inspect current status.
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
          {canCreateRoom && (
            <button
              onClick={() => {
                setShowCreateModal(true);
                setFormError("");
              }}
              style={{
                ...buttonStyle,
                background: "#0f766e",
                fontWeight: 600,
              }}
            >
              + Add Room
            </button>
          )}

          <button onClick={loadRooms} style={buttonStyle} disabled={loading}>
            {loading ? "Loading..." : "Refresh"}
          </button>

          <Link to="/dashboard" style={linkStyle}>
            Dashboard
          </Link>
        </div>
      </div>

      {successMessage && (
        <div
          style={{
            background: "#dcfce7",
            color: "#166534",
            padding: "12px 18px",
            borderRadius: "8px",
            marginBottom: "20px",
            border: "1px solid #bbf7d0",
            fontWeight: 500,
          }}
        >
          {successMessage}
        </div>
      )}

      {message && <p style={{ color: "#b91c1c" }}>{message}</p>}

      {/* Modal for Creating Room */}
      {showCreateModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            background: "rgba(15, 23, 42, 0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: "20px",
            boxSizing: "border-box",
          }}
        >
          <div
            style={{
              background: "#ffffff",
              borderRadius: "14px",
              padding: "28px",
              width: "100%",
              maxWidth: "500px",
              boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.1)",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "20px",
              }}
            >
              <h2 style={{ margin: 0, fontSize: "20px", color: "#17243a" }}>
                Add New Room
              </h2>
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                style={{
                  background: "transparent",
                  border: "none",
                  fontSize: "20px",
                  cursor: "pointer",
                  color: "#64748b",
                }}
              >
                ✕
              </button>
            </div>

            {formError && (
              <p
                style={{
                  color: "#b91c1c",
                  background: "#fee2e2",
                  padding: "10px",
                  borderRadius: "6px",
                  fontSize: "14px",
                  marginBottom: "16px",
                }}
              >
                {formError}
              </p>
            )}

            <form onSubmit={handleCreateRoom}>
              <div style={{ marginBottom: "16px" }}>
                <label style={labelStyle}>Hotel Property</label>
                {hotels.length > 0 ? (
                  <select
                    name="hotel_id"
                    value={newRoom.hotel_id}
                    onChange={handleInputChange}
                    style={inputStyle}
                    required
                  >
                    {hotels.map((h) => (
                      <option key={h.id} value={h.id}>
                        {h.name} (Code: {h.code})
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    type="number"
                    name="hotel_id"
                    value={newRoom.hotel_id || 1}
                    onChange={handleInputChange}
                    placeholder="Enter Hotel ID (e.g. 1)"
                    style={inputStyle}
                    required
                  />
                )}
              </div>

              <div style={{ marginBottom: "16px" }}>
                <label style={labelStyle}>Room Type</label>
                {roomTypes.length > 0 ? (
                  <select
                    name="room_type_id"
                    value={newRoom.room_type_id}
                    onChange={handleInputChange}
                    style={inputStyle}
                    required
                  >
                    {roomTypes.map((rt) => (
                      <option key={rt.id} value={rt.id}>
                        {rt.name} - ₹{rt.base_price}/night (Capacity: {rt.capacity})
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    type="number"
                    name="room_type_id"
                    value={newRoom.room_type_id || 1}
                    onChange={handleInputChange}
                    placeholder="Enter Room Type ID (e.g. 1)"
                    style={inputStyle}
                    required
                  />
                )}
              </div>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: "14px",
                  marginBottom: "24px",
                }}
              >
                <div>
                  <label style={labelStyle}>Room Number</label>
                  <input
                    type="text"
                    name="room_number"
                    value={newRoom.room_number}
                    onChange={handleInputChange}
                    placeholder="e.g. 105"
                    style={inputStyle}
                    required
                  />
                </div>

                <div>
                  <label style={labelStyle}>Floor Number</label>
                  <input
                    type="number"
                    name="floor"
                    value={newRoom.floor}
                    onChange={handleInputChange}
                    placeholder="e.g. 1"
                    min="1"
                    style={inputStyle}
                    required
                  />
                </div>
              </div>

              <div
                style={{
                  display: "flex",
                  justifyContent: "flex-end",
                  gap: "12px",
                }}
              >
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  style={{
                    ...buttonStyle,
                    background: "#f1f5f9",
                    color: "#475569",
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  style={{
                    ...buttonStyle,
                    background: "#0f766e",
                  }}
                >
                  {submitting ? "Saving..." : "Create Room"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

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
  fontSize: "14px",
};

const linkStyle = {
  background: "#ffffff",
  color: "#0f766e",
  border: "1px solid #0f766e",
  padding: "10px 18px",
  borderRadius: "8px",
  textDecoration: "none",
  fontSize: "14px",
  display: "inline-flex",
  alignItems: "center",
};

const labelStyle = {
  display: "block",
  fontSize: "13px",
  fontWeight: 600,
  color: "#334155",
  marginBottom: "6px",
};

const inputStyle = {
  width: "100%",
  padding: "10px 12px",
  borderRadius: "8px",
  border: "1px solid #cbd5e1",
  fontSize: "14px",
  boxSizing: "border-box",
  background: "#ffffff",
  color: "#1e293b",
};

export default Rooms;
