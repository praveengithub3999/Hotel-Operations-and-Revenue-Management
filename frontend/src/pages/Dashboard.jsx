
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../services/api";
import "./Dashboard.css";

function Dashboard() {
  const [rooms, setRooms] = useState([]);
  const [reservations, setReservations] = useState([]);
  const [guests, setGuests] = useState([]);
  const [message, setMessage] = useState("");

  const navigate = useNavigate();

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
      "/dashboard", "/rooms", "/guests", "/reservations",
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
      "/dashboard", "/rooms", "/reservations", "/reports",
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

      // Load only information the role is expected to access.
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
        setMessage("Some dashboard information could not be loaded.");
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
        <h2>StayEase</h2>

        <nav>
          {navigationLinks.map((item) => (
            <Link key={item.path} to={item.path}>
              {item.label}
            </Link>
          ))}
        </nav>

        <button
          type="button"
          onClick={handleLogout}
          style={{
            marginTop: "25px",
            width: "100%",
            padding: "10px",
            cursor: "pointer",
          }}
        >
          Logout
        </button>
      </aside>

      <main className="main-content">
        <div className="header">
          <div>
            <h1>Hotel Dashboard</h1>
            <p>Welcome to StayEase Hotel Management</p>
          </div>

          <span>{role.replaceAll("_", " ")}</span>
        </div>

        {message && <p>{message}</p>}

        {["ADMIN", "RECEPTIONIST", "MANAGER"].includes(role) && (
          <div className="cards">
            <div className="card">
              <h3>Total Rooms</h3>
              <p>{rooms.length}</p>
              <Link to="/rooms">View rooms</Link>
            </div>

            <div className="card">
              <h3>Total Reservations</h3>
              <p>{reservations.length}</p>
              <Link to="/reservations">View reservations</Link>
            </div>

            {["ADMIN", "RECEPTIONIST"].includes(role) && (
              <div className="card">
                <h3>Total Guests</h3>
                <p>{guests.length}</p>
                <Link to="/guests">View guests</Link>
              </div>
            )}
          </div>
        )}

        {["ADMIN", "FINANCE"].includes(role) && (
          <div className="cards">
            <div className="card">
              <h3>Billing</h3>
              <p>Invoices and payments</p>
              <Link to="/billing">Open billing</Link>
            </div>
          </div>
        )}

        {["ADMIN", "HOUSEKEEPING"].includes(role) && (
          <div className="cards">
            <div className="card">
              <h3>Housekeeping</h3>
              <p>Room cleaning tasks</p>
              <Link to="/housekeeping">View tasks</Link>
            </div>
          </div>
        )}

        {["ADMIN", "MAINTENANCE"].includes(role) && (
          <div className="cards">
            <div className="card">
              <h3>Maintenance</h3>
              <p>Room repair requests</p>
              <Link to="/maintenance">View maintenance</Link>
            </div>
          </div>
        )}

        {["ADMIN", "MANAGER", "FINANCE"].includes(role) && (
          <div className="cards">
            <div className="card">
              <h3>Reports</h3>
              <p>Hotel performance</p>
              <Link to="/reports">View reports</Link>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default Dashboard;
