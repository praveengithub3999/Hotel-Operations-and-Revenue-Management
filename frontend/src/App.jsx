import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  Outlet,
} from "react-router-dom";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Rooms from "./pages/Rooms";
import Guests from "./pages/Guests";
import Reservations from "./pages/Reservations";
import Billing from "./pages/Billing";
import Housekeeping from "./pages/Housekeeping";
import Maintenance from "./pages/Maintenance";
import Reports from "./pages/Reports";

function ProtectedRoute() {
  const token = localStorage.getItem("token");

  return token ? <Outlet /> : <Navigate to="/" replace />;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/rooms" element={<Rooms />} />
          <Route path="/guests" element={<Guests />} />
          <Route path="/reservations" element={<Reservations />} />
          <Route path="/billing" element={<Billing />} />
          <Route path="/housekeeping" element={<Housekeeping />} />
          <Route path="/maintenance" element={<Maintenance />} />
          <Route path="/reports" element={<Reports />} />
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
