import { useCallback, useEffect, useState } from "react";
import api from "../services/api";

function Housekeeping() {
  const [tasks, setTasks] = useState([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [loadingTask, setLoadingTask] = useState(null);

  const loadTasks = useCallback(async () => {
    try {
      const response = await api.get("/housekeeping/");
      setTasks(response.data);
      setMessage("");
    } catch (error) {
      console.error(error);
      setMessage("Unable to load housekeeping tasks.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      void loadTasks();
    }, 0);

    return () => clearTimeout(timer);
  }, [loadTasks]);

  const updateTask = async (taskId, status) => {
    setLoadingTask(taskId);
    setMessage("");

    try {
      await api.put(`/housekeeping/${taskId}`, { status });
      setMessage(`Task #${taskId} updated successfully.`);
      await loadTasks();
    } catch (error) {
      console.error(error);
      setMessage(
        error.response?.data?.detail ||
          "Unable to update housekeeping task."
      );
    } finally {
      setLoadingTask(null);
    }
  };

  const getStatusClass = (status) => {
    const classes = {
      DIRTY: "dirty",
      CLEANING_IN_PROGRESS: "cleaning",
      INSPECTED: "inspected",
      CLEAN: "clean",
    };

    return classes[status] || "default";
  };

  const getStatusLabel = (status) => status.replaceAll("_", " ");

  const dirtyCount = tasks.filter((task) => task.status === "DIRTY").length;

  const cleaningCount = tasks.filter(
    (task) => task.status === "CLEANING_IN_PROGRESS"
  ).length;

  const completedCount = tasks.filter(
    (task) => task.status === "CLEAN"
  ).length;

  return (
    <div className="hk-page">
      <style>{`
        .hk-page {
          padding: 30px;
          min-height: 100vh;
          background: #f4f7fb;
          color: #17243a;
          box-sizing: border-box;
        }

        .hk-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 16px;
          flex-wrap: wrap;
          margin-bottom: 25px;
        }

        .hk-header h1 {
          font-size: 30px;
          margin: 0 0 8px;
          color: #17243a;
        }

        .hk-subtitle {
          margin: 0;
          color: #718096;
          font-size: 14px;
        }

        .hk-button {
          background: #0f766e;
          color: white;
          border: none;
          border-radius: 8px;
          padding: 11px 17px;
          font-weight: 600;
          cursor: pointer;
        }

        .hk-button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .hk-stats {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 18px;
          margin-bottom: 25px;
        }

        .hk-stat {
          background: white;
          border: 1px solid #e7ecf3;
          border-radius: 12px;
          padding: 21px;
          box-shadow: 0 3px 12px rgba(23, 36, 58, 0.04);
        }

        .hk-stat-label {
          color: #718096;
          font-size: 13px;
          margin: 0 0 12px;
        }

        .hk-stat-value {
          font-size: 27px;
          font-weight: 700;
          margin: 0;
        }

        .hk-panel {
          background: white;
          border: 1px solid #e7ecf3;
          border-radius: 12px;
          padding: 22px;
          box-shadow: 0 3px 12px rgba(23, 36, 58, 0.04);
        }

        .hk-panel-heading {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 12px;
          flex-wrap: wrap;
          margin-bottom: 18px;
        }

        .hk-panel-heading h2 {
          margin: 0;
          font-size: 19px;
        }

        .hk-count {
          background: #e6fffa;
          color: #0f766e;
          padding: 6px 10px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: 700;
        }

        .hk-table-wrap {
          width: 100%;
          overflow-x: auto;
        }

        .hk-table {
          width: 100%;
          border-collapse: collapse;
          min-width: 850px;
        }

        .hk-table th {
          text-align: left;
          color: #718096;
          background: #f8fafc;
          font-size: 12px;
          font-weight: 600;
          padding: 14px 12px;
          border-bottom: 1px solid #e7ecf3;
          white-space: nowrap;
        }

        .hk-table td {
          padding: 16px 12px;
          border-bottom: 1px solid #edf1f6;
          font-size: 13px;
          vertical-align: middle;
        }

        .hk-table tr:last-child td {
          border-bottom: none;
        }

        .hk-task-id {
          font-weight: 700;
          color: #17243a;
        }

        .hk-room {
          display: inline-block;
          background: #edf2f7;
          color: #334155;
          padding: 5px 9px;
          border-radius: 6px;
          font-weight: 600;
        }

        .hk-status {
          display: inline-block;
          padding: 6px 9px;
          border-radius: 20px;
          font-size: 11px;
          font-weight: 700;
          white-space: nowrap;
        }

        .hk-status.dirty {
          background: #fff1f0;
          color: #c53030;
        }

        .hk-status.cleaning {
          background: #fff7e6;
          color: #ad6800;
        }

        .hk-status.inspected {
          background: #e6f4ff;
          color: #0958a5;
        }

        .hk-status.clean {
          background: #e6fffa;
          color: #0f766e;
        }

        .hk-status.default {
          background: #edf2f7;
          color: #475569;
        }

        .hk-select {
          padding: 9px 10px;
          border: 1px solid #d7dfeb;
          border-radius: 7px;
          background: white;
          color: #334155;
          max-width: 190px;
          width: 100%;
          font-size: 12px;
        }

        .hk-select:disabled {
          opacity: 0.6;
        }

        .hk-message {
          background: #e6fffa;
          color: #0f766e;
          padding: 12px 15px;
          border-radius: 8px;
          margin-bottom: 20px;
          font-size: 13px;
        }

        .hk-message.error {
          background: #fff1f0;
          color: #c53030;
        }

        .hk-empty {
          text-align: center;
          padding: 45px 15px;
          color: #718096;
          font-size: 14px;
        }

        @media (max-width: 1000px) {
          .hk-stats {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }
        }

        @media (max-width: 600px) {
          .hk-page {
            padding: 18px;
          }

          .hk-header h1 {
            font-size: 25px;
          }

          .hk-stats {
            grid-template-columns: 1fr;
            gap: 12px;
          }

          .hk-panel {
            padding: 15px;
          }
        }
      `}</style>

      <div className="hk-header">
        <div>
          <h1>Housekeeping Management</h1>
          <p className="hk-subtitle">
            Track room cleaning, inspections and room readiness.
          </p>
        </div>

        <button
          className="hk-button"
          type="button"
          onClick={loadTasks}
          disabled={loading}
        >
          {loading ? "Loading..." : "↻ Refresh Tasks"}
        </button>
      </div>

      {message && (
        <div
          role="status"
          className={`hk-message ${
            message.toLowerCase().includes("unable") ||
            message.toLowerCase().includes("error")
              ? "error"
              : ""
          }`}
        >
          {message}
        </div>
      )}

      <div className="hk-stats">
        <div className="hk-stat">
          <p className="hk-stat-label">Total Tasks</p>
          <p className="hk-stat-value">{tasks.length}</p>
        </div>

        <div className="hk-stat">
          <p className="hk-stat-label">Rooms Awaiting Cleaning</p>
          <p className="hk-stat-value" style={{ color: "#c53030" }}>
            {dirtyCount}
          </p>
        </div>

        <div className="hk-stat">
          <p className="hk-stat-label">Cleaning In Progress</p>
          <p className="hk-stat-value" style={{ color: "#ad6800" }}>
            {cleaningCount}
          </p>
        </div>

        <div className="hk-stat">
          <p className="hk-stat-label">Completed Tasks</p>
          <p className="hk-stat-value" style={{ color: "#0f766e" }}>
            {completedCount}
          </p>
        </div>
      </div>

      <div className="hk-panel">
        <div className="hk-panel-heading">
          <h2>All Housekeeping Tasks</h2>
          <span className="hk-count">{tasks.length} tasks</span>
        </div>

        {loading ? (
          <div className="hk-empty">Loading housekeeping tasks...</div>
        ) : tasks.length === 0 ? (
          <div className="hk-empty">
            No housekeeping tasks found.
            <p>Tasks will appear here when rooms require cleaning.</p>
          </div>
        ) : (
          <div className="hk-table-wrap">
            <table className="hk-table">
              <thead>
                <tr>
                  <th>Task</th>
                  <th>Room ID</th>
                  <th>Status</th>
                  <th>Assigned To</th>
                  <th>Notes</th>
                  <th>Completed At</th>
                  <th>Update Status</th>
                </tr>
              </thead>

              <tbody>
                {tasks.map((task) => (
                  <tr key={task.id}>
                    <td className="hk-task-id">#{task.id}</td>
                    <td>
                      <span className="hk-room">{task.room_id}</span>
                    </td>
                    <td>
                      <span
                        className={`hk-status ${getStatusClass(task.status)}`}
                      >
                        {getStatusLabel(task.status)}
                      </span>
                    </td>
                    <td>{task.assigned_to || "Unassigned"}</td>
                    <td>{task.notes || "—"}</td>
                    <td>
                      {task.completed_at
                        ? new Date(task.completed_at).toLocaleString()
                        : "—"}
                    </td>
                    <td>
                      <select
                        className="hk-select"
                        aria-label={`Update status for task ${task.id}`}
                        value={task.status}
                        disabled={loadingTask === task.id}
                        onChange={(event) =>
                          updateTask(task.id, event.target.value)
                        }
                      >
                        <option value="DIRTY">Dirty</option>
                        <option value="CLEANING_IN_PROGRESS">
                          Cleaning In Progress
                        </option>
                        <option value="INSPECTED">Inspected</option>
                        <option value="CLEAN">Clean</option>
                      </select>

                      {loadingTask === task.id && (
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

export default Housekeeping;
