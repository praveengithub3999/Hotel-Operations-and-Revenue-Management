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

  useEffect(() => {
    const token = localStorage.getItem("token");

    const headers = {
      Authorization: `Bearer ${token}`,
    };

    const loadDashboardData = async () => {
      try {
        const [roomsResponse, reservationsResponse, guestsResponse] =
          await Promise.all([
            api.get("/rooms/", { headers }),
            api.get("/reservations/", { headers }),
            api.get("/guests/", { headers }),
          ]);

        setRooms(roomsResponse.data);
        setReservations(reservationsResponse.data);
        setGuests(guestsResponse.data);
      } catch (error) {
        console.error("Failed to load dashboard data:", error);

        if (error.response?.status === 401) {
          localStorage.removeItem("token");
          navigate("/", { replace: true });
        } else {
          setMessage("Unable to load dashboard information.");
        }
      }
    };

    loadDashboardData();
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/", { replace: true });
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
  ];

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

          <span>Admin</span>
        </div>

        {message && <p>{message}</p>}

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

          <div className="card">
            <h3>Total Guests</h3>
            <p>{guests.length}</p>
            <Link to="/guests">View guests</Link>
          </div>

          <div className="card">
            <h3>Billing</h3>
            <p>Invoices and payments</p>
            <Link to="/billing">Open billing</Link>
          </div>

          <div className="card">
            <h3>Housekeeping</h3>
            <p>Room cleaning tasks</p>
            <Link to="/housekeeping">View tasks</Link>
          </div>

          <div className="card">
            <h3>Maintenance</h3>
            <p>Room repair requests</p>
            <Link to="/maintenance">View maintenance</Link>
          </div>

          <div className="card">
            <h3>Reports</h3>
            <p>Hotel performance</p>
            <Link to="/reports">View reports</Link>
          </div>
        </div>
      </main>
    </div>
  );
}

export default Dashboard;
