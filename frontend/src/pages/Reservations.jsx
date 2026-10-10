import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

function Reservations() {
  const [reservations, setReservations] = useState([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingReservations, setLoadingReservations] = useState(true);
  const [processingId, setProcessingId] = useState(null);

  const [form, setForm] = useState({
    guest_id: "",
    room_id: "",
    check_in_date: "",
    check_out_date: "",
    number_of_guests: 1,
    special_requests: "",
  });

  const navigate = useNavigate();

  const getHeaders = () => ({
    Authorization: `Bearer ${localStorage.getItem("token")}`,
  });

  const loadReservations = async () => {
    setLoadingReservations(true);

    try {
      const response = await api.get("/reservations/", {
        headers: getHeaders(),
      });

      setReservations(response.data);
      setMessage("");
    } catch (error) {
      console.error(error);

      if (error.response?.status === 401) {
        localStorage.removeItem("token");
        navigate("/", { replace: true });
        return;
      }

      setMessage("Unable to load reservations.");
    } finally {
      setLoadingReservations(false);
    }
  };

  useEffect(() => {
    loadReservations();
  }, []);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setForm((previousForm) => ({
      ...previousForm,
      [name]:
        ["guest_id", "room_id", "number_of_guests"].includes(name)
          ? Number(value)
          : value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setMessage("");

    if (form.check_out_date <= form.check_in_date) {
      setMessage("Check-out date must be after check-in date.");
      return;
    }

    setLoading(true);

    try {
      await api.post("/reservations/", form, {
        headers: getHeaders(),
      });

      setMessage("Reservation created successfully!");

      setForm({
        guest_id: "",
        room_id: "",
        check_in_date: "",
        check_out_date: "",
        number_of_guests: 1,
        special_requests: "",
      });

      await loadReservations();
    } catch (error) {
      setMessage(
        error.response?.data?.detail ||
          "Failed to create reservation."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleCheckIn = async (reservationId) => {
    setMessage("");
    setProcessingId(reservationId);

    try {
      await api.post(
        `/reservations/${reservationId}/check-in`,
        {},
        { headers: getHeaders() }
      );

      setMessage(
        `Reservation #${reservationId} checked in successfully.`
      );

      await loadReservations();
    } catch (error) {
      setMessage(
        error.response?.data?.detail || "Check-in failed."
      );
    } finally {
      setProcessingId(null);
    }
  };

  const handleCheckout = async (reservationId) => {
    const confirmed = window.confirm(
      `Check out Reservation #${reservationId}? Make sure its invoice is paid.`
    );

    if (!confirmed) return;

    setMessage("");
    setProcessingId(reservationId);

    try {
      await api.post(
        `/checkout/${reservationId}`,
        {},
        { headers: getHeaders() }
      );

      setMessage(
        `Reservation #${reservationId} checked out successfully. The room is now awaiting housekeeping.`
      );

      await loadReservations();
    } catch (error) {
      setMessage(
        error.response?.data?.detail || "Checkout failed."
      );
    } finally {
      setProcessingId(null);
    }
  };

  const statusColors = {
    PENDING: { background: "#fef3c7", color: "#92400e" },
    CONFIRMED: { background: "#dbeafe", color: "#1d4ed8" },
    CHECKED_IN: { background: "#d1fae5", color: "#065f46" },
    CHECKED_OUT: { background: "#e2e8f0", color: "#334155" },
    CANCELLED: { background: "#fee2e2", color: "#991b1b" },
    NO_SHOW: { background: "#f3e8ff", color: "#6b21a8" },
  };

  const cardStyle = {
    background: "#ffffff",
    border: "1px solid #e5eaf1",
    borderRadius: "12px",
    padding: "22px",
    boxShadow: "0 3px 12px rgba(15, 23, 42, 0.035)",
  };

  const inputStyle = {
    width: "100%",
    padding: "11px 12px",
    marginTop: "7px",
    border: "1px solid #cbd5e1",
    borderRadius: "7px",
    boxSizing: "border-box",
    background: "#ffffff",
    color: "#17243a",
  };

  const labelStyle = {
    display: "block",
    color: "#475569",
    fontSize: "14px",
    fontWeight: 600,
  };

  const buttonStyle = {
    background: "#0f766e",
    color: "#ffffff",
    border: "none",
    padding: "10px 16px",
    borderRadius: "7px",
    cursor: "pointer",
    fontWeight: 600,
  };

  const countByStatus = (status) =>
    reservations.filter((reservation) => reservation.status === status)
      .length;

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
      {/* Page heading */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "15px",
          marginBottom: "28px",
        }}
      >
        <div>
          <h1
            style={{
              margin: "0 0 8px",
              fontSize: "30px",
              lineHeight: 1.3,
            }}
          >
            Reservation Management
          </h1>

          <p
            style={{
              color: "#64748b",
              margin: 0,
              fontSize: "14px",
            }}
          >
            Create reservations and manage guest check-in and check-out.
          </p>
        </div>

        <button
          type="button"
          onClick={loadReservations}
          disabled={loadingReservations}
          style={buttonStyle}
        >
          {loadingReservations ? "Loading..." : "Refresh"}
        </button>
      </div>

      {message && (
        <div
          role="status"
          style={{
            background: "#ffffff",
            border: "1px solid #dbe5ef",
            padding: "13px 16px",
            borderRadius: "8px",
            marginBottom: "22px",
          }}
        >
          {message}
        </div>
      )}

      {/* Reservation summary */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
          gap: "16px",
          marginBottom: "28px",
        }}
      >
        {[
          { label: "Total Reservations", value: reservations.length },
          { label: "Confirmed", value: countByStatus("CONFIRMED") },
          { label: "Checked In", value: countByStatus("CHECKED_IN") },
          { label: "Checked Out", value: countByStatus("CHECKED_OUT") },
          { label: "Cancelled", value: countByStatus("CANCELLED") },
        ].map((item) => (
          <div key={item.label} style={cardStyle}>
            <p
              style={{
                color: "#64748b",
                fontSize: "13px",
                margin: "0 0 12px",
              }}
            >
              {item.label}
            </p>

            <h2 style={{ margin: 0, fontSize: "28px" }}>
              {item.value}
            </h2>
          </div>
        ))}
      </div>

      {/* Create reservation form */}
      <section style={{ ...cardStyle, marginBottom: "28px" }}>
        <h2 style={{ margin: "0 0 8px", fontSize: "21px" }}>
          Create Reservation
        </h2>

        <p
          style={{
            color: "#64748b",
            fontSize: "14px",
            marginBottom: "24px",
          }}
        >
          Enter guest, room, and stay details.
        </p>

        <form onSubmit={handleSubmit}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              gap: "20px",
            }}
          >
            <label style={labelStyle}>
              Guest ID
              <input
                style={inputStyle}
                type="number"
                name="guest_id"
                min="1"
                value={form.guest_id}
                onChange={handleChange}
                required
              />
            </label>

            <label style={labelStyle}>
              Room ID
              <input
                style={inputStyle}
                type="number"
                name="room_id"
                min="1"
                value={form.room_id}
                onChange={handleChange}
                required
              />
            </label>

            <label style={labelStyle}>
              Check-in Date
              <input
                style={inputStyle}
                type="date"
                name="check_in_date"
                value={form.check_in_date}
                onChange={handleChange}
                required
              />
            </label>

            <label style={labelStyle}>
              Check-out Date
              <input
                style={inputStyle}
                type="date"
                name="check_out_date"
                value={form.check_out_date}
                onChange={handleChange}
                required
              />
            </label>

            <label style={labelStyle}>
              Number of Guests
              <input
                style={inputStyle}
                type="number"
                name="number_of_guests"
                min="1"
                value={form.number_of_guests}
                onChange={handleChange}
                required
              />
            </label>

            <label style={labelStyle}>
              Special Requests
              <input
                style={inputStyle}
                type="text"
                name="special_requests"
                value={form.special_requests}
                onChange={handleChange}
                placeholder="Optional requests"
              />
            </label>
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{ ...buttonStyle, marginTop: "24px" }}
          >
            {loading ? "Creating..." : "Create Reservation"}
          </button>
        </form>
      </section>

      {/* Reservations table */}
      <section style={cardStyle}>
        <h2 style={{ margin: "0 0 20px", fontSize: "21px" }}>
          All Reservations
        </h2>

        {loadingReservations ? (
          <p>Loading reservations...</p>
        ) : reservations.length === 0 ? (
          <p>No reservations found.</p>
        ) : (
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
                  {[
                    "Reservation",
                    "Guest ID",
                    "Room ID",
                    "Check-in",
                    "Check-out",
                    "Status",
                    "Action",
                  ].map((heading) => (
                    <th
                      key={heading}
                      style={{
                        padding: "14px 12px",
                        borderBottom: "1px solid #e5eaf1",
                        fontSize: "13px",
                        color: "#475569",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {heading}
                    </th>
                  ))}
                </tr>
              </thead>

              <tbody>
                {reservations.map((reservation) => (
                  <tr key={reservation.id}>
                    <td style={tableCellStyle}>
                      <strong>#{reservation.id}</strong>
                    </td>

                    <td style={tableCellStyle}>
                      {reservation.guest_id}
                    </td>

                    <td style={tableCellStyle}>
                      {reservation.room_id}
                    </td>

                    <td style={tableCellStyle}>
                      {reservation.check_in_date}
                    </td>

                    <td style={tableCellStyle}>
                      {reservation.check_out_date}
                    </td>

                    <td style={tableCellStyle}>
                      <span
                        style={{
                          ...(statusColors[reservation.status] || {
                            background: "#f1f5f9",
                            color: "#334155",
                          }),
                          padding: "6px 10px",
                          borderRadius: "20px",
                          fontSize: "11px",
                          fontWeight: 700,
                          whiteSpace: "nowrap",
                        }}
                      >
                        {reservation.status.replaceAll("_", " ")}
                      </span>
                    </td>

                    <td style={tableCellStyle}>
                      {reservation.status === "CONFIRMED" && (
                        <button
                          type="button"
                          disabled={processingId === reservation.id}
                          onClick={() => handleCheckIn(reservation.id)}
                          style={buttonStyle}
                        >
                          {processingId === reservation.id
                            ? "Processing..."
                            : "Check-in"}
                        </button>
                      )}

                      {reservation.status === "CHECKED_IN" && (
                        <button
                          type="button"
                          disabled={processingId === reservation.id}
                          onClick={() => handleCheckout(reservation.id)}
                          style={buttonStyle}
                        >
                          {processingId === reservation.id
                            ? "Processing..."
                            : "Check-out"}
                        </button>
                      )}

                      {["CHECKED_OUT", "CANCELLED", "NO_SHOW"].includes(
                        reservation.status
                      ) && (
                        <span style={{ color: "#94a3b8" }}>—</span>
                      )}

                      {reservation.status === "PENDING" && (
                        <span style={{ color: "#64748b" }}>
                          Awaiting confirmation
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

const tableCellStyle = {
  padding: "14px 12px",
  borderBottom: "1px solid #e5eaf1",
  fontSize: "13px",
  whiteSpace: "nowrap",
};

export default Reservations;