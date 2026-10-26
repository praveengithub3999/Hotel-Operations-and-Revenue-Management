import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import api from "../services/api";
import "./Dashboard.css";

function Dashboard() {
  const [rooms, setRooms] = useState([]);
  const [reservations, setReservations] = useState([]);
  const [guests, setGuests] = useState([]);
  const [message, setMessage] = useState("");

  const navigate = useNavigate();
  const location = useLocation();

  // Read the role from the current login token.
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

  const roleLinks = {
    ADMIN: [
      "/dashboard", "/rooms", "/guests", "/reservations",
      "/billing", "/housekeeping", "/maintenance", "/reports",
    ],
    RECEPTIONIST: [
      "/dashboard", "/rooms", "/guests", "/reservations", "/billing",
    ],
    HOUSEKEEPING: [
      "/dashboard", "/housekeeping",
    ],
    MAINTENANCE: [
      "/dashboard", "/maintenance",
    ],
    FINANCE: [
      "/dashboard", "/billing", "/reports",
    ],
    MANAGER: [
      "/dashboard", "/rooms", "/reservations", "/billing", "/reports",
    ],
  };

  const navigationLinks = [
    { path: "/dashboard", label: "Dashboard" },
    { path: "/rooms", label: "Rooms" },
    { path: "/guests", label: "Guests" },
    { path: "/reservations", label: "Reservations" },
    { path: "/billing", label: "Billing & Invoices" },
    { path: "/housekeeping", label: "Housekeeping" },
    { path: "/maintenance", label: "Maintenance" },
    { path: "/reports", label: "Reports" },
  ].filter((item) => (roleLinks[role] || ["/dashboard"]).includes(item.path));

  useEffect(() => {
    if (!token || !role) {
      localStorage.removeItem("token");
      navigate("/", { replace: true });
      return;
    }

    const loadDashboardData = async () => {
      setMessage("");

      const requests = [];

      if (["ADMIN", "RECEPTIONIST", "MANAGER"].includes(role)) {
        requests.push(
          api.get("/rooms/").then((response) => setRooms(response.data))
        );
      }

      if (["ADMIN", "RECEPTIONIST", "MANAGER"].includes(role)) {
        requests.push(
          api.get("/reservations/").then((response) =>
            setReservations(response.data)
          )
        );
      }

      if (["ADMIN", "RECEPTIONIST"].includes(role)) {
        requests.push(
          api.get("/guests/").then((response) => setGuests(response.data))
        );
      }

      if (requests.length === 0) {
        setMessage(
          role === "MAINTENANCE"
            ? "Welcome to Maintenance. Open Maintenance to manage repair requests."
            : role === "HOUSEKEEPING"
              ? "Welcome to Housekeeping. Open Housekeeping to view cleaning tasks."
              : "Welcome to your dashboard."
        );
        return;
      }

      const results = await Promise.allSettled(requests);
      const failedRequests = results.filter(
        (result) => result.status === "rejected"
      );

      if (failedRequests.length > 0) {
        console.error("Some dashboard requests failed:", failedRequests);
        setMessage("Some dashboard metrics could not be loaded.");
      }
    };

    loadDashboardData().catch((error) => {
      console.error("Failed to load dashboard data:", error);

      if (error.response?.status === 401) {
        localStorage.removeItem("token");
        navigate("/", { replace: true });
      } else {
        setMessage("Unable to load dashboard information.");
      }
    });
  }, [navigate, role, token]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/", { replace: true });
  };

  return (
    <div className="dashboard">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span>🏨</span> StayEase
        </div>

        <nav>
          {navigationLinks.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={location.pathname === item.path ? "active" : ""}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <button
          type="button"
          onClick={handleLogout}
          className="sidebar-logout-btn"
        >
          Sign Out
        </button>
      </aside>

      <main className="main-content">
        <div className="dashboard-header">
          <div>
            <h1>Hotel Operations Dashboard</h1>
            <p>Welcome to StayEase Hotel Management System</p>
          </div>

          <span className="role-badge">{role.replaceAll("_", " ")}</span>
        </div>

        {message && <div className="dashboard-banner">{message}</div>}

        {/* Top Summary Metrics */}
        {["ADMIN", "RECEPTIONIST", "MANAGER"].includes(role) && (
          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-label">Total Rooms</span>
              <div className="stat-value">{rooms.length}</div>
              <Link to="/rooms" className="stat-link">
                View rooms →
              </Link>
            </div>

            <div className="stat-card">
              <span className="stat-label">Total Reservations</span>
              <div className="stat-value">{reservations.length}</div>
              <Link to="/reservations" className="stat-link">
                View reservations →
              </Link>
            </div>

            {["ADMIN", "RECEPTIONIST"].includes(role) && (
              <div className="stat-card">
                <span className="stat-label">Total Guests</span>
                <div className="stat-value">{guests.length}</div>
                <Link to="/guests" className="stat-link">
                  View guests →
                </Link>
              </div>
            )}
          </div>
        )}

        {/* Operational Modules Section */}
        <h2 className="section-heading">Operational Modules</h2>

        <div className="modules-grid">
          {["ADMIN", "RECEPTIONIST", "MANAGER"].includes(role) && (
            <div className="module-card">
              <div className="module-icon">🏨</div>
              <h3 className="module-title">Rooms &amp; Inventory</h3>
              <p className="module-desc">
                Manage room configurations, floors, availability, and pricing.
              </p>
              <Link to="/rooms" className="module-link">
                Manage Rooms →
              </Link>
            </div>
          )}

          {["ADMIN", "RECEPTIONIST", "MANAGER"].includes(role) && (
            <div className="module-card">
              <div className="module-icon">📅</div>
              <h3 className="module-title">Reservations</h3>
              <p className="module-desc">
                Handle bookings, check-in, check-out, and stay modifications.
              </p>
              <Link to="/reservations" className="module-link">
                Manage Reservations →
              </Link>
            </div>
          )}

          {["ADMIN", "RECEPTIONIST"].includes(role) && (
            <div className="module-card">
              <div className="module-icon">👤</div>
              <h3 className="module-title">Guest Registry</h3>
              <p className="module-desc">
                Register guest profiles, verify ID proofs, and track stay history.
              </p>
              <Link to="/guests" className="module-link">
                View Guests →
              </Link>
            </div>
          )}

          {["ADMIN", "FINANCE", "RECEPTIONIST", "MANAGER"].includes(role) && (
            <div className="module-card">
              <div className="module-icon">💳</div>
              <h3 className="module-title">Billing &amp; Invoices</h3>
              <p className="module-desc">
                Review folios, generate invoices, apply discounts, and record payments.
              </p>
              <Link to="/billing" className="module-link">
                Open Billing →
              </Link>
            </div>
          )}

          {["ADMIN", "HOUSEKEEPING", "MANAGER"].includes(role) && (
            <div className="module-card">
              <div className="module-icon">🧹</div>
              <h3 className="module-title">Housekeeping</h3>
              <p className="module-desc">
                Monitor room hygiene, track cleaning tasks, and inspect rooms.
              </p>
              <Link to="/housekeeping" className="module-link">
                View Tasks →
              </Link>
            </div>
          )}

          {["ADMIN", "MAINTENANCE", "MANAGER"].includes(role) && (
            <div className="module-card">
              <div className="module-icon">🔧</div>
              <h3 className="module-title">Maintenance</h3>
              <p className="module-desc">
                Track room repair requests, assign technicians, and monitor SLAs.
              </p>
              <Link to="/maintenance" className="module-link">
                View Maintenance →
              </Link>
            </div>
          )}

          {["ADMIN", "MANAGER", "FINANCE"].includes(role) && (
            <div className="module-card">
              <div className="module-icon">📊</div>
              <h3 className="module-title">Reports &amp; Analytics</h3>
              <p className="module-desc">
                Analyze hotel occupancy rates, ADR, RevPAR, and revenue breakdown.
              </p>
              <Link to="/reports" className="module-link">
                View Reports →
              </Link>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default Dashboard;
