
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

function Reports() {
  const [occupancy, setOccupancy] = useState(null);
  const [revenue, setRevenue] = useState(null);
  const [reservations, setReservations] = useState(null);
  const [rooms, setRooms] = useState(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const loadReports = async () => {
    setLoading(true);
    setMessage("");

    try {
      const token = localStorage.getItem("token");
      const config = {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      };

      const [
        occupancyResponse,
        revenueResponse,
        reservationsResponse,
        roomsResponse,
      ] = await Promise.all([
        api.get("/reports/occupancy", config),
        api.get("/reports/revenue", config),
        api.get("/reports/reservations", config),
        api.get("/reports/rooms", config),
      ]);

      setOccupancy(occupancyResponse.data);
      setRevenue(revenueResponse.data);
      setReservations(reservationsResponse.data);
      setRooms(roomsResponse.data);
    } catch (error) {
      console.error(error);

      if (error.response?.status === 401) {
        localStorage.removeItem("token");
        navigate("/");
        return;
      }

      setMessage(
        error.response?.data?.detail ||
          "Unable to load reports. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  const formatMoney = (amount) =>
    Number(amount || 0).toLocaleString("en-IN", {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });

  const formatNumber = (value) =>
    Number(value || 0).toLocaleString("en-IN");

  const StatCard = ({ title, value, subtitle, accent = "#17243a" }) => (
    <div className="rp-stat">
      <p className="rp-stat-label">{title}</p>
      <h3 style={{ color: accent }}>{value ?? 0}</h3>
      {subtitle && <p className="rp-stat-subtitle">{subtitle}</p>}
    </div>
  );

  const Section = ({ title, description, children }) => (
    <section className="rp-section">
      <div className="rp-section-heading">
        <div>
          <h2>{title}</h2>
          {description && <p>{description}</p>}
        </div>
      </div>
      {children}
    </section>
  );

  const roomStatusItems = rooms
    ? [
        { label: "Available", value: rooms.available, color: "#0f766e" },
        { label: "Reserved", value: rooms.reserved, color: "#2563eb" },
        { label: "Occupied", value: rooms.occupied, color: "#7c3aed" },
        { label: "Dirty", value: rooms.dirty, color: "#dc2626" },
        { label: "Cleaning", value: rooms.cleaning, color: "#d97706" },
        {
          label: "Maintenance",
          value: rooms.maintenance,
          color: "#64748b",
        },
      ]
    : [];

  const reservationItems = reservations
    ? [
        { label: "Pending", value: reservations.pending },
        { label: "Confirmed", value: reservations.confirmed },
        { label: "Checked In", value: reservations.checked_in },
        { label: "Checked Out", value: reservations.checked_out },
        { label: "Cancelled", value: reservations.cancelled },
        { label: "No Show", value: reservations.no_show },
      ]
    : [];

  const occupancyPercentage = Math.max(
    0,
    Math.min(100, Number(occupancy?.occupancy_percentage || 0))
  );

  if (loading) {
    return (
      <div className="rp-page">
        <style>{`
          .rp-page {
            min-height: 100vh;
            padding: 30px;
            background: #f4f7fb;
            color: #17243a;
            box-sizing: border-box;
          }
          .rp-loading {
            background: white;
            border: 1px solid #e7ecf3;
            border-radius: 12px;
            padding: 35px;
            color: #718096;
          }
        `}</style>
        <div className="rp-loading">Loading hotel reports...</div>
      </div>
    );
  }

  return (
    <div className="rp-page">
      <style>{`
        .rp-page {
          min-height: 100vh;
          padding: 30px;
          background: #f4f7fb;
          color: #17243a;
          box-sizing: border-box;
        }

        .rp-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          flex-wrap: wrap;
          gap: 16px;
          margin-bottom: 25px;
        }

        .rp-header h1 {
          margin: 0 0 8px;
          font-size: 30px;
          color: #17243a;
        }

        .rp-subtitle {
          margin: 0;
          color: #718096;
          font-size: 14px;
        }

        .rp-button {
          background: #0f766e;
          color: white;
          border: none;
          border-radius: 8px;
          padding: 11px 17px;
          font-size: 13px;
          font-weight: 600;
          cursor: pointer;
        }

        .rp-button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .rp-section {
          margin-bottom: 28px;
        }

        .rp-section-heading {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          margin-bottom: 16px;
        }

        .rp-section-heading h2 {
          margin: 0;
          font-size: 20px;
          color: #17243a;
        }

        .rp-section-heading p {
          margin: 6px 0 0;
          color: #718096;
          font-size: 13px;
        }

        .rp-grid {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 17px;
        }

        .rp-stat {
          min-width: 0;
          padding: 21px;
          background: white;
          border: 1px solid #e7ecf3;
          border-radius: 12px;
          box-shadow: 0 3px 12px rgba(23, 36, 58, 0.04);
        }

        .rp-stat-label {
          margin: 0 0 12px;
          color: #718096;
          font-size: 13px;
        }

        .rp-stat h3 {
          margin: 0;
          font-size: 25px;
          overflow-wrap: anywhere;
        }

        .rp-stat-subtitle {
          margin: 9px 0 0;
          color: #718096;
          font-size: 12px;
          line-height: 1.5;
        }

        .rp-panel {
          padding: 23px;
          background: white;
          border: 1px solid #e7ecf3;
          border-radius: 12px;
          box-shadow: 0 3px 12px rgba(23, 36, 58, 0.04);
        }

        .rp-occupancy-layout {
          display: grid;
          grid-template-columns: minmax(0, 1fr) minmax(0, 1.4fr);
          gap: 28px;
          align-items: center;
        }

        .rp-progress-labels {
          display: flex;
          justify-content: space-between;
          gap: 10px;
          margin-bottom: 12px;
          font-size: 13px;
          color: #718096;
        }

        .rp-progress-track {
          width: 100%;
          height: 12px;
          background: #e8eef5;
          border-radius: 20px;
          overflow: hidden;
        }

        .rp-progress-fill {
          height: 100%;
          background: #0f766e;
          border-radius: 20px;
          transition: width 0.3s ease;
        }

        .rp-status-list {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 13px;
        }

        .rp-status-item {
          padding: 15px;
          border: 1px solid #e7ecf3;
          border-radius: 9px;
          background: #fbfcfe;
        }

        .rp-status-name {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #718096;
          font-size: 12px;
          margin-bottom: 10px;
        }

        .rp-status-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          flex-shrink: 0;
        }

        .rp-status-value {
          font-size: 22px;
          font-weight: 700;
          color: #17243a;
        }

        .rp-message {
          padding: 13px 15px;
          margin-bottom: 22px;
          border-radius: 8px;
          background: #fff1f0;
          color: #c53030;
          font-size: 13px;
        }

        @media (max-width: 1100px) {
          .rp-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }

          .rp-occupancy-layout {
            grid-template-columns: 1fr;
          }
        }

        @media (max-width: 650px) {
          .rp-page {
            padding: 18px;
          }

          .rp-header h1 {
            font-size: 25px;
          }

          .rp-grid {
            grid-template-columns: 1fr;
          }

          .rp-status-list {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }

          .rp-panel {
            padding: 16px;
          }
        }
      `}</style>

      <div className="rp-header">
        <div>
          <h1>Reports & Analytics</h1>
          <p className="rp-subtitle">
            Monitor hotel occupancy, revenue, reservations and room status.
          </p>
        </div>

        <button
          className="rp-button"
          onClick={loadReports}
          disabled={loading}
        >
          ↻ Refresh Reports
        </button>
      </div>

      {message && <div className="rp-message">{message}</div>}

      {occupancy && (
        <Section
          title="Occupancy Overview"
          description="Current room utilization across the hotel."
        >
          <div className="rp-grid" style={{ marginBottom: 17 }}>
            <StatCard
              title="Total Rooms"
              value={formatNumber(occupancy.total_rooms)}
            />
            <StatCard
              title="Occupied Rooms"
              value={formatNumber(occupancy.occupied_rooms)}
              accent="#7c3aed"
            />
            <StatCard
              title="Available Rooms"
              value={formatNumber(occupancy.available_rooms)}
              accent="#0f766e"
            />
            <StatCard
              title="Occupancy Rate"
              value={`${occupancy.occupancy_percentage ?? 0}%`}
              accent="#2563eb"
            />
          </div>

          <div className="rp-panel">
            <div className="rp-occupancy-layout">
              <div>
                <p style={{ margin: "0 0 9px", color: "#718096", fontSize: 13 }}>
                  Overall occupancy
                </p>
                <h3 style={{ margin: "0 0 10px", fontSize: 30 }}>
                  {occupancy.occupancy_percentage ?? 0}%
                </h3>
                <p style={{ margin: 0, color: "#718096", fontSize: 13 }}>
                  {formatNumber(occupancy.occupied_rooms)} occupied out of{" "}
                  {formatNumber(occupancy.total_rooms)} total rooms.
                </p>
              </div>

              <div>
                <div className="rp-progress-labels">
                  <span>Room utilization</span>
                  <strong>{occupancyPercentage}%</strong>
                </div>

                <div
                  className="rp-progress-track"
                  role="progressbar"
                  aria-label="Occupancy percentage"
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={occupancyPercentage}
                >
                  <div
                    className="rp-progress-fill"
                    style={{ width: `${occupancyPercentage}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </Section>
      )}

      {revenue && (
        <Section
          title="Revenue Overview"
          description="Financial figures returned by the backend report."
        >
          <div className="rp-grid">
            <StatCard
              title="Total Charges"
              value={formatMoney(revenue.total_charges)}
              accent="#2563eb"
              subtitle="Charges recorded in the system"
            />
            <StatCard
              title="Successful Payments"
              value={formatMoney(revenue.successful_payments)}
              accent="#0f766e"
              subtitle="Payments processed successfully"
            />
            <StatCard
              title="Total Revenue"
              value={formatMoney(revenue.total_revenue)}
              accent="#0f766e"
              subtitle="Based on successful payments"
            />
          </div>
        </Section>
      )}

      {reservations && (
        <Section
          title="Reservation Overview"
          description="Distribution of reservations by their current status."
        >
          <div className="rp-grid">
            <StatCard
              title="Total Reservations"
              value={formatNumber(reservations.total_reservations)}
            />

            {reservationItems.map((item) => (
              <StatCard
                key={item.label}
                title={item.label}
                value={formatNumber(item.value)}
                accent={
                  item.label === "Checked In"
                    ? "#7c3aed"
                    : item.label === "Cancelled" ||
                        item.label === "No Show"
                      ? "#dc2626"
                      : "#17243a"
                }
              />
            ))}
          </div>
        </Section>
      )}

      {rooms && (
        <Section
          title="Room Status Report"
          description="Current room counts by operational status."
        >
          <div className="rp-panel">
            <div className="rp-status-list">
              {roomStatusItems.map((item) => (
                <div className="rp-status-item" key={item.label}>
                  <div className="rp-status-name">
                    <span
                      className="rp-status-dot"
                      style={{ background: item.color }}
                    />
                    {item.label}
                  </div>
                  <div className="rp-status-value">
                    {formatNumber(item.value)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Section>
      )}

      {!occupancy && !revenue && !reservations && !rooms && !message && (
        <div className="rp-panel">
          No report data is currently available.
        </div>
      )}
    </div>
  );
}

export default Reports;
