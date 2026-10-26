import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../services/api";

function Guests() {
  const [guests, setGuests] = useState([]);
  const [message, setMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

  const [newGuest, setNewGuest] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    address: "",
    id_type: "PASSPORT",
    id_reference: "",
    emergency_contact: "",
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

  const canCreateGuest = ["ADMIN", "RECEPTIONIST"].includes(role);

  const loadGuests = useCallback(async () => {
    setLoading(true);

    try {
      const response = await api.get("/guests/");
      setGuests(response.data);
      setMessage("");
    } catch (error) {
      console.error(error);
      setMessage("Unable to load guests. Please try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      void loadGuests();
    }, 0);

    return () => clearTimeout(timer);
  }, [loadGuests]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNewGuest((prev) => ({ ...prev, [name]: value }));
  };

  const handleCreateGuest = async (e) => {
    e.preventDefault();
    setFormError("");
    setSuccessMessage("");

    if (!newGuest.first_name.trim() || !newGuest.last_name.trim()) {
      setFormError("First name and Last name are required.");
      return;
    }

    if (!newGuest.email.trim() && !newGuest.phone.trim()) {
      setFormError("At least an email or phone number is required.");
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        first_name: newGuest.first_name.trim(),
        last_name: newGuest.last_name.trim(),
        email: newGuest.email.trim() || null,
        phone: newGuest.phone.trim() || null,
        address: newGuest.address.trim() || null,
        id_type: newGuest.id_type,
        id_reference: newGuest.id_reference.trim() || null,
        emergency_contact: newGuest.emergency_contact.trim() || null,
      };

      await api.post("/guests/", payload);

      setSuccessMessage(
        `Guest ${payload.first_name} ${payload.last_name} registered successfully!`
      );
      setShowCreateModal(false);
      setNewGuest({
        first_name: "",
        last_name: "",
        email: "",
        phone: "",
        address: "",
        id_type: "PASSPORT",
        id_reference: "",
        emergency_contact: "",
      });

      await loadGuests();
    } catch (err) {
      console.error(err);
      let errorMsg = "Failed to register guest. Please check details.";
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
            Register new guest profiles, view contact records, and verify IDs.
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
          {canCreateGuest && (
            <button
              type="button"
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
              + Register Guest
            </button>
          )}

          <button
            type="button"
            onClick={loadGuests}
            disabled={loading}
            style={buttonStyle}
          >
            {loading ? "Loading..." : "Refresh Guests"}
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

      {message && (
        <p style={{ color: "#b91c1c", marginBottom: "20px" }}>{message}</p>
      )}

      {/* Register Guest Modal */}
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
              maxWidth: "560px",
              boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.1)",
              maxHeight: "90vh",
              overflowY: "auto",
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
                Register New Guest
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

            <form onSubmit={handleCreateGuest}>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: "14px",
                  marginBottom: "16px",
                }}
              >
                <div>
                  <label style={labelStyle}>First Name *</label>
                  <input
                    type="text"
                    name="first_name"
                    value={newGuest.first_name}
                    onChange={handleInputChange}
                    placeholder="e.g. Ramesh"
                    style={inputStyle}
                    required
                  />
                </div>

                <div>
                  <label style={labelStyle}>Last Name *</label>
                  <input
                    type="text"
                    name="last_name"
                    value={newGuest.last_name}
                    onChange={handleInputChange}
                    placeholder="e.g. Sharma"
                    style={inputStyle}
                    required
                  />
                </div>
              </div>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: "14px",
                  marginBottom: "16px",
                }}
              >
                <div>
                  <label style={labelStyle}>Email Address</label>
                  <input
                    type="email"
                    name="email"
                    value={newGuest.email}
                    onChange={handleInputChange}
                    placeholder="guest@example.com"
                    style={inputStyle}
                  />
                </div>

                <div>
                  <label style={labelStyle}>Phone Number *</label>
                  <input
                    type="tel"
                    name="phone"
                    value={newGuest.phone}
                    onChange={handleInputChange}
                    placeholder="e.g. 9876543210"
                    style={inputStyle}
                    required
                  />
                </div>
              </div>

              <div style={{ marginBottom: "16px" }}>
                <label style={labelStyle}>Address</label>
                <input
                  type="text"
                  name="address"
                  value={newGuest.address}
                  onChange={handleInputChange}
                  placeholder="Street, City, State, Country"
                  style={inputStyle}
                />
              </div>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: "14px",
                  marginBottom: "16px",
                }}
              >
                <div>
                  <label style={labelStyle}>ID Proof Type</label>
                  <select
                    name="id_type"
                    value={newGuest.id_type}
                    onChange={handleInputChange}
                    style={inputStyle}
                  >
                    <option value="PASSPORT">Passport</option>
                    <option value="AADHAAR">Aadhaar Card</option>
                    <option value="DRIVING_LICENSE">Driving License</option>
                    <option value="NATIONAL_ID">National ID</option>
                    <option value="VOTER_ID">Voter ID</option>
                  </select>
                </div>

                <div>
                  <label style={labelStyle}>ID Reference Number</label>
                  <input
                    type="text"
                    name="id_reference"
                    value={newGuest.id_reference}
                    onChange={handleInputChange}
                    placeholder="e.g. PASS-987654"
                    style={inputStyle}
                  />
                </div>
              </div>

              <div style={{ marginBottom: "24px" }}>
                <label style={labelStyle}>Emergency Contact</label>
                <input
                  type="tel"
                  name="emergency_contact"
                  value={newGuest.emergency_contact}
                  onChange={handleInputChange}
                  placeholder="Emergency phone or contact info"
                  style={inputStyle}
                />
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
                  {submitting ? "Registering..." : "Register Guest"}
                </button>
              </div>
            </form>
          </div>
        </div>
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
          <p style={{ color: "#64748b", margin: "0 0 10px" }}>TOTAL GUESTS</p>
          <h2 style={{ margin: 0, fontSize: "30px" }}>{guests.length}</h2>
        </div>

        <div style={cardStyle}>
          <p style={{ color: "#64748b", margin: "0 0 10px" }}>EMAIL RECORDS</p>
          <h2 style={{ margin: 0, fontSize: "30px" }}>
            {guests.filter((guest) => guest.email).length}
          </h2>
        </div>

        <div style={cardStyle}>
          <p style={{ color: "#64748b", margin: "0 0 10px" }}>PHONE RECORDS</p>
          <h2 style={{ margin: 0, fontSize: "30px" }}>
            {guests.filter((guest) => guest.phone).length}
          </h2>
        </div>
      </div>

      <div style={cardStyle}>
        <h2 style={{ margin: "0 0 20px", fontSize: "21px" }}>All Guests</h2>

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
                  <th style={cellStyle}>ID Reference</th>
                  <th style={cellStyle}>Emergency Contact</th>
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
                    <td style={cellStyle}>{guest.email || "Not provided"}</td>
                    <td style={cellStyle}>{guest.phone || "Not provided"}</td>
                    <td style={cellStyle}>
                      {guest.id_reference
                        ? `${guest.id_type || "ID"}: ${guest.id_reference}`
                        : "None"}
                    </td>
                    <td style={cellStyle}>
                      {guest.emergency_contact || "Not provided"}
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

const buttonStyle = {
  background: "#0f766e",
  color: "#ffffff",
  border: "none",
  padding: "11px 18px",
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

export default Guests;
