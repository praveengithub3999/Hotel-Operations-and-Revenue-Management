
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

function Maintenance() {
  const [tasks, setTasks] = useState([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [updatingTask, setUpdatingTask] = useState(null);
  const [assignments, setAssignments] = useState({});
  const navigate = useNavigate();

  const [form, setForm] = useState({
    room_id: "",
    issue: "",
    assigned_to: "",
    notes: "",
  });

  const getHeaders = () => ({
    Authorization: `Bearer ${localStorage.getItem("token")}`,
  });

  const loadTasks = async () => {
    try {
      const response = await api.get("/maintenance/", {
        headers: getHeaders(),
      });

      setTasks(response.data);

      setAssignments((previous) => {
        const updated = { ...previous };

        response.data.forEach((task) => {
          if (!(task.id in updated)) {
            updated[task.id] = task.assigned_to || "";
          }
        });

        return updated;
      });

      setMessage("");
    } catch (error) {
      console.error(error);

      if (error.response?.status === 401) {
        localStorage.removeItem("token");
        navigate("/");
        return;
      }

      setMessage("Unable to load maintenance tasks.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
  }, []);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setCreating(true);
    setMessage("");

    try {
      await api.post(
        "/maintenance/",
        {
          room_id: Number(form.room_id),
          issue: form.issue.trim(),
          assigned_to: form.assigned_to.trim() || null,
          notes: form.notes.trim() || null,
        },
        { headers: getHeaders() }
      );

      setMessage("Maintenance request created successfully!");

      setForm({
        room_id: "",
        issue: "",
        assigned_to: "",
        notes: "",
      });

      await loadTasks();
    } catch (error) {
      console.error(error);
      setMessage(
        error.response?.data?.detail ||
          "Failed to create maintenance request."
      );
    } finally {
      setCreating(false);
    }
  };

  const updateTask = async (taskId, status) => {
    const task = tasks.find((item) => item.id === taskId);

    if (!task) return;

    setUpdatingTask(taskId);
    setMessage("");

    try {
      await api.put(
        `/maintenance/${taskId}`,
        {
          status,
          assigned_to: assignments[taskId]?.trim() || null,
          notes: task.notes || null,
        },
        { headers: getHeaders() }
      );

      setMessage(`Maintenance task #${taskId} updated successfully.`);
      await loadTasks();
    } catch (error) {
      console.error(error);
      setMessage(
        error.response?.data?.detail ||
          "Failed to update maintenance task."
      );
    } finally {
      setUpdatingTask(null);
    }
  };

  const updateAssignee = async (task) => {
    const assignedTo = (assignments[task.id] || "").trim();

    if (assignedTo === (task.assigned_to || "")) return;

    setUpdatingTask(task.id);
    setMessage("");

    try {
      await api.put(
        `/maintenance/${task.id}`,
        {
          status: task.status,
          assigned_to: assignedTo || null,
          notes: task.notes || null,
        },
        { headers: getHeaders() }
      );

      setMessage(`Assignment updated for task #${task.id}.`);
      await loadTasks();
    } catch (error) {
      console.error(error);
      setMessage(
        error.response?.data?.detail ||
          "Failed to update assignment."
      );
    } finally {
      setUpdatingTask(null);
    }
  };

  const getStatusClass = (status) => {
    const classes = {
      OPEN: "open",
      ASSIGNED: "assigned",
      IN_PROGRESS: "progress",
      ON_HOLD: "hold",
      RESOLVED: "resolved",
      CLOSED: "closed",
      CANCELLED: "cancelled",
    };

    return classes[status] || "default";
  };

  const getStatusLabel = (status) =>
    status.replaceAll("_", " ");

  const openCount = tasks.filter(
    (task) => task.status === "OPEN"
  ).length;

  const activeCount = tasks.filter(
    (task) =>
      task.status === "ASSIGNED" ||
      task.status === "IN_PROGRESS"
  ).length;

  const resolvedCount = tasks.filter(
    (task) =>
      task.status === "RESOLVED" ||
      task.status === "CLOSED"
  ).length;

  const activeStatuses = [
    "OPEN",
    "ASSIGNED",
    "IN_PROGRESS",
    "ON_HOLD",
  ];

  const showError =
    message.toLowerCase().includes("unable") ||
    message.toLowerCase().includes("failed") ||
    message.toLowerCase().includes("error");

  return (
    <div className="mt-page">
      <style>{`
        .mt-page {
          min-height: 100vh;
          padding: 30px;
          box-sizing: border-box;
          background: #f4f7fb;
          color: #17243a;
        }

        .mt-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          flex-wrap: wrap;
          gap: 16px;
          margin-bottom: 25px;
        }

        .mt-header h1 {
          margin: 0 0 8px;
          font-size: 30px;
          color: #17243a;
        }

        .mt-subtitle {
          margin: 0;
          color: #718096;
          font-size: 14px;
        }

        .mt-button {
          padding: 11px 17px;
          border: none;
          border-radius: 8px;
          background: #0f766e;
          color: white;
          font-size: 13px;
          font-weight: 600;
          cursor: pointer;
        }

        .mt-button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .mt-stats {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 18px;
          margin-bottom: 25px;
        }

        .mt-stat {
          padding: 21px;
          background: white;
          border: 1px solid #e7ecf3;
          border-radius: 12px;
          box-shadow: 0 3px 12px rgba(23, 36, 58, 0.04);
        }

        .mt-stat-label {
          margin: 0 0 12px;
          color: #718096;
          font-size: 13px;
        }

        .mt-stat-value {
          margin: 0;
          font-size: 27px;
          font-weight: 700;
        }

        .mt-panel {
          padding: 23px;
          background: white;
          border: 1px solid #e7ecf3;
          border-radius: 12px;
          box-shadow: 0 3px 12px rgba(23, 36, 58, 0.04);
          margin-bottom: 25px;
        }

        .mt-panel-heading {
          display: flex;
          justify-content: space-between;
          align-items: center;
          flex-wrap: wrap;
          gap: 12px;
          margin-bottom: 20px;
        }

        .mt-panel-heading h2 {
          margin: 0;
          font-size: 19px;
          color: #17243a;
        }

        .mt-count {
          padding: 6px 10px;
          border-radius: 20px;
          background: #e6fffa;
          color: #0f766e;
          font-size: 12px;
          font-weight: 700;
        }

        .mt-form {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 18px;
        }

        .mt-field {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .mt-field label {
          color: #475569;
          font-size: 13px;
          font-weight: 600;
        }

        .mt-field input,
        .mt-field textarea {
          width: 100%;
          box-sizing: border-box;
          padding: 11px 12px;
          border: 1px solid #d7dfeb;
          border-radius: 8px;
          background: white;
          color: #17243a;
          font-family: inherit;
          font-size: 13px;
        }

        .mt-field input:focus,
        .mt-field textarea:focus {
          outline: 2px solid #b2f5ea;
          border-color: #0f766e;
        }

        .mt-field textarea {
          resize: vertical;
          min-height: 42px;
        }

        .mt-form-footer {
          grid-column: 1 / -1;
          display: flex;
          justify-content: flex-end;
        }

        .mt-table-wrap {
          overflow-x: auto;
          width: 100%;
        }

        .mt-table {
          width: 100%;
          min-width: 1050px;
          border-collapse: collapse;
        }

        .mt-table th {
          padding: 14px 12px;
          text-align: left;
          background: #f8fafc;
          border-bottom: 1px solid #e7ecf3;
          color: #718096;
          font-size: 12px;
          font-weight: 600;
          white-space: nowrap;
        }

        .mt-table td {
          padding: 15px 12px;
          border-bottom: 1px solid #edf1f6;
          font-size: 13px;
          vertical-align: middle;
        }

        .mt-table tr:last-child td {
          border-bottom: none;
        }

        .mt-task-id {
          color: #17243a;
          font-weight: 700;
        }

        .mt-room {
          display: inline-block;
          padding: 5px 9px;
          border-radius: 6px;
          background: #edf2f7;
          color: #334155;
          font-weight: 600;
        }

        .mt-status {
          display: inline-block;
          padding: 6px 9px;
          border-radius: 20px;
          font-size: 11px;
          font-weight: 700;
          white-space: nowrap;
        }

        .mt-status.open {
          background: #fff1f0;
          color: #c53030;
        }

        .mt-status.assigned {
          background: #e6f4ff;
          color: #0958a5;
        }

        .mt-status.progress {
          background: #fff7e6;
          color: #ad6800;
        }

        .mt-status.hold {
          background: #f3e8ff;
          color: #7e22ce;
        }

        .mt-status.resolved,
        .mt-status.closed {
          background: #e6fffa;
          color: #0f766e;
        }

        .mt-status.cancelled {
          background: #edf2f7;
          color: #64748b;
        }

        .mt-status.default {
          background: #edf2f7;
          color: #475569;
        }

        .mt-control {
          width: 100%;
          min-width: 145px;
          box-sizing: border-box;
          padding: 9px 10px;
          border: 1px solid #d7dfeb;
          border-radius: 7px;
          background: white;
          color: #334155;
          font-size: 12px;
        }

        .mt-control:disabled {
          opacity: 0.6;
        }

        .mt-message {
          padding: 12px 15px;
          margin-bottom: 20px;
          border-radius: 8px;
          background: #e6fffa;
          color: #0f766e;
          font-size: 13px;
        }

        .mt-message.error {
          background: #fff1f0;
          color: #c53030;
        }

        .mt-empty {
          padding: 35px 15px;
          text-align: center;
          color: #718096;
          font-size: 14px;
        }

        @media (max-width: 1000px) {
          .mt-stats {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }
        }

        @media (max-width: 600px) {
          .mt-page {
            padding: 18px;
          }

          .mt-header h1 {
            font-size: 25px;
          }

          .mt-stats,
          .mt-form {
            grid-template-columns: 1fr;
          }

          .mt-panel {
            padding: 15px;
          }
        }
      `}</style>

      <div className="mt-header">
        <div>
          <h1>Maintenance Management</h1>
          <p className="mt-subtitle">
            Report room issues, assign staff and track repairs.
          </p>
        </div>

        <button
          className="mt-button"
          onClick={() => {
            setLoading(true);
            loadTasks();
          }}
          disabled={loading}
        >
          {loading ? "Loading..." : "↻ Refresh Tasks"}
        </button>
      </div>

      {message && (
        <div className={`mt-message ${showError ? "error" : ""}`}>
          {message}
        </div>
      )}

      <div className="mt-stats">
        <div className="mt-stat">
          <p className="mt-stat-label">Total Requests</p>
          <p className="mt-stat-value">{tasks.length}</p>
        </div>

        <div className="mt-stat">
          <p className="mt-stat-label">Open Requests</p>
          <p className="mt-stat-value" style={{ color: "#c53030" }}>
            {openCount}
          </p>
        </div>

        <div className="mt-stat">
          <p className="mt-stat-label">Active Work</p>
          <p className="mt-stat-value" style={{ color: "#ad6800" }}>
            {activeCount}
          </p>
        </div>

        <div className="mt-stat">
          <p className="mt-stat-label">Resolved / Closed</p>
          <p className="mt-stat-value" style={{ color: "#0f766e" }}>
            {resolvedCount}
          </p>
        </div>
      </div>

      <div className="mt-panel">
        <div className="mt-panel-heading">
          <h2>Create Maintenance Request</h2>
        </div>

        <form className="mt-form" onSubmit={handleSubmit}>
          <div className="mt-field">
            <label htmlFor="room_id">Room ID *</label>
            <input
              id="room_id"
              type="number"
              name="room_id"
              min="1"
              value={form.room_id}
              onChange={handleChange}
              placeholder="Enter room ID"
              required
            />
          </div>

          <div className="mt-field">
            <label htmlFor="issue">Issue Description *</label>
            <input
              id="issue"
              type="text"
              name="issue"
              value={form.issue}
              onChange={handleChange}
              placeholder="e.g. Air conditioner not working"
              required
            />
          </div>

          <div className="mt-field">
            <label htmlFor="assigned_to">Assign Staff (optional)</label>
            <input
              id="assigned_to"
              type="text"
              name="assigned_to"
              value={form.assigned_to}
              onChange={handleChange}
              placeholder="Enter staff name"
            />
          </div>

          <div className="mt-field">
            <label htmlFor="notes">Additional Notes (optional)</label>
            <textarea
              id="notes"
              name="notes"
              value={form.notes}
              onChange={handleChange}
              placeholder="Add any useful details"
              rows="2"
            />
          </div>

          <div className="mt-form-footer">
            <button
              className="mt-button"
              type="submit"
              disabled={creating}
            >
              {creating ? "Creating..." : "+ Create Request"}
            </button>
          </div>
        </form>
      </div>

      <div className="mt-panel">
        <div className="mt-panel-heading">
          <h2>All Maintenance Tasks</h2>
          <span className="mt-count">{tasks.length} tasks</span>
        </div>

        {loading ? (
          <div className="mt-empty">Loading maintenance tasks...</div>
        ) : tasks.length === 0 ? (
          <div className="mt-empty">
            No maintenance tasks found.
            <p>Create a request above when a room needs repairs.</p>
          </div>
        ) : (
          <div className="mt-table-wrap">
            <table className="mt-table">
              <thead>
                <tr>
                  <th>Task</th>
                  <th>Room ID</th>
                  <th>Issue</th>
                  <th>Status</th>
                  <th>Assigned To</th>
                  <th>Notes</th>
                  <th>Resolved At</th>
                  <th>Update Status</th>
                </tr>
              </thead>

              <tbody>
                {tasks.map((task) => (
                  <tr key={task.id}>
                    <td className="mt-task-id">#{task.id}</td>

                    <td>
                      <span className="mt-room">{task.room_id}</span>
                    </td>

                    <td>{task.issue}</td>

                    <td>
                      <span
                        className={`mt-status ${getStatusClass(task.status)}`}
                      >
                        {getStatusLabel(task.status)}
                      </span>
                    </td>

                    <td>
                      <input
                        className="mt-control"
                        aria-label={`Assignee for task ${task.id}`}
                        value={assignments[task.id] ?? ""}
                        placeholder="Staff name"
                        disabled={updatingTask === task.id}
                        onChange={(event) =>
                          setAssignments((previous) => ({
                            ...previous,
                            [task.id]: event.target.value,
                          }))
                        }
                        onBlur={() => updateAssignee(task)}
                      />
                    </td>

                    <td>{task.notes || "—"}</td>

                    <td>
                      {task.resolved_at
                        ? new Date(task.resolved_at).toLocaleString()
                        : "—"}
                    </td>

                    <td>
                      <select
                        className="mt-control"
                        aria-label={`Update status for task ${task.id}`}
                        value={task.status}
                        disabled={updatingTask === task.id}
                        onChange={(event) =>
                          updateTask(task.id, event.target.value)
                        }
                      >
                        <option value="OPEN">Open</option>
                        <option value="ASSIGNED">Assigned</option>
                        <option value="IN_PROGRESS">In Progress</option>
                        <option value="ON_HOLD">On Hold</option>
                        <option value="RESOLVED">Resolved</option>
                        <option value="CLOSED">Closed</option>
                        <option value="CANCELLED">Cancelled</option>
                      </select>

                      {updatingTask === task.id && (
                        <p style={{ margin: "5px 0 0", color: "#718096" }}>
                          Updating...
                        </p>
                      )}
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

export default Maintenance;
