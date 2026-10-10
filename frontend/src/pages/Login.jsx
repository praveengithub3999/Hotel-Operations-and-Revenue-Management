
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

function Login() {
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleLogin = async (event) => {
    event.preventDefault();
    setMessage("");
    setLoading(true);

    try {
      const response = await api.post("/auth/login", {
        username: username.trim(),
        password,
      });

      localStorage.setItem("token", response.data.access_token);
      navigate("/dashboard", { replace: true });
    } catch (error) {
      console.error(error);

      setMessage(
        error.response?.data?.detail ||
          "Login failed. Please check your credentials and try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <style>{`
        .login-page {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 24px;
          box-sizing: border-box;
          background:
            radial-gradient(circle at top left, #24466b 0, transparent 38%),
            linear-gradient(135deg, #111d32, #17243a 55%, #0f766e);
          font-family: Arial, Helvetica, sans-serif;
        }

        .login-layout {
          width: 100%;
          max-width: 960px;
          display: grid;
          grid-template-columns: 1fr 0.9fr;
          overflow: hidden;
          border-radius: 20px;
          background: white;
          box-shadow: 0 25px 70px rgba(0, 0, 0, 0.25);
        }

        .login-brand {
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          padding: 48px 40px;
          color: white;
          background: linear-gradient(155deg, #17243a, #203d55);
        }

        .login-brand-name {
          display: flex;
          align-items: center;
          gap: 12px;
          font-size: 21px;
          font-weight: 700;
          letter-spacing: 0.3px;
        }

        .login-brand-icon {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 43px;
          height: 43px;
          border-radius: 12px;
          background: #0f766e;
          font-size: 23px;
        }

        .login-brand-content {
          margin: 55px 0;
        }

        .login-brand-content h1 {
          margin: 0 0 18px;
          font-size: 35px;
          line-height: 1.25;
          color: white;
        }

        .login-brand-content p {
          margin: 0;
          color: #cbd5e1;
          font-size: 15px;
          line-height: 1.8;
        }

        .login-features {
          display: grid;
          gap: 15px;
          margin-top: 30px;
        }

        .login-feature {
          display: flex;
          align-items: center;
          gap: 11px;
          color: #e2e8f0;
          font-size: 13px;
        }

        .login-feature-icon {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 25px;
          height: 25px;
          flex-shrink: 0;
          border-radius: 50%;
          background: rgba(15, 118, 110, 0.35);
          color: #5eead4;
          font-weight: 700;
        }

        .login-brand-footer {
          color: #a8b8cc;
          font-size: 12px;
        }

        .login-form-panel {
          display: flex;
          flex-direction: column;
          justify-content: center;
          padding: 48px 38px;
        }

        .login-form-panel h2 {
          margin: 0 0 10px;
          color: #17243a;
          font-size: 28px;
        }

        .login-description {
          margin: 0 0 30px;
          color: #718096;
          font-size: 14px;
          line-height: 1.6;
        }

        .login-field {
          margin-bottom: 21px;
        }

        .login-field label {
          display: block;
          margin-bottom: 9px;
          color: #334155;
          font-size: 13px;
          font-weight: 600;
        }

        .login-input {
          width: 100%;
          box-sizing: border-box;
          padding: 13px 14px;
          border: 1px solid #d7dfeb;
          border-radius: 9px;
          background: #fbfcfe;
          color: #17243a;
          font-size: 14px;
          outline: none;
          transition: border-color 0.2s, box-shadow 0.2s;
        }

        .login-input:focus {
          border-color: #0f766e;
          box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.12);
        }

        .login-password-wrap {
          position: relative;
        }

        .login-password-wrap .login-input {
          padding-right: 75px;
        }

        .login-show-password {
          position: absolute;
          top: 50%;
          right: 12px;
          transform: translateY(-50%);
          padding: 5px;
          border: none;
          background: transparent;
          color: #0f766e;
          font-size: 12px;
          font-weight: 600;
          cursor: pointer;
        }

        .login-error {
          margin: 0 0 18px;
          padding: 12px;
          border-radius: 8px;
          background: #fff1f0;
          color: #c53030;
          font-size: 13px;
          line-height: 1.5;
        }

        .login-submit {
          width: 100%;
          padding: 14px;
          margin-top: 4px;
          border: none;
          border-radius: 9px;
          background: #0f766e;
          color: white;
          font-size: 14px;
          font-weight: 700;
          cursor: pointer;
          transition: background 0.2s;
        }

        .login-submit:hover:not(:disabled) {
          background: #115e59;
        }

        .login-submit:disabled {
          opacity: 0.65;
          cursor: not-allowed;
        }

        .login-security-note {
          margin: 23px 0 0;
          text-align: center;
          color: #718096;
          font-size: 12px;
          line-height: 1.6;
        }

        @media (max-width: 720px) {
          .login-layout {
            max-width: 440px;
            grid-template-columns: 1fr;
          }

          .login-brand {
            padding: 25px;
          }

          .login-brand-content {
            margin: 30px 0 20px;
          }

          .login-brand-content h1 {
            font-size: 27px;
          }

          .login-features,
          .login-brand-footer {
            display: none;
          }

          .login-form-panel {
            padding: 32px 25px;
          }
        }

        @media (max-width: 400px) {
          .login-page {
            padding: 12px;
          }

          .login-form-panel {
            padding: 27px 20px;
          }
        }
      `}</style>

      <div className="login-layout">
        <div className="login-brand">
          <div className="login-brand-name">
            <div className="login-brand-icon">⌂</div>
            <span>StayEase</span>
          </div>

          <div className="login-brand-content">
            <h1>Hotel operations, made simpler.</h1>

            <p>
              Manage rooms, reservations, billing and daily hotel
              operations from one central workspace.
            </p>

            <div className="login-features">
              <div className="login-feature">
                <span className="login-feature-icon">✓</span>
                Room and reservation management
              </div>

              <div className="login-feature">
                <span className="login-feature-icon">✓</span>
                Billing and payment tracking
              </div>

              <div className="login-feature">
                <span className="login-feature-icon">✓</span>
                Housekeeping and maintenance
              </div>

              <div className="login-feature">
                <span className="login-feature-icon">✓</span>
                Reports and hotel analytics
              </div>
            </div>
          </div>

          <div className="login-brand-footer">
            StayEase Hotel Operations & Revenue Management
          </div>
        </div>

        <div className="login-form-panel">
          <h2>Welcome back</h2>

          <p className="login-description">
            Sign in to access your hotel management dashboard.
          </p>

          <form onSubmit={handleLogin}>
            <div className="login-field">
              <label htmlFor="username">Username</label>

              <input
                id="username"
                className="login-input"
                type="text"
                autoComplete="username"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                placeholder="Enter your username"
                required
                autoFocus
              />
            </div>

            <div className="login-field">
              <label htmlFor="password">Password</label>

              <div className="login-password-wrap">
                <input
                  id="password"
                  className="login-input"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Enter your password"
                  required
                />

                <button
                  className="login-show-password"
                  type="button"
                  onClick={() => setShowPassword((previous) => !previous)}
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
            </div>

            {message && (
              <div className="login-error" role="alert">
                {message}
              </div>
            )}

            <button
              className="login-submit"
              type="submit"
              disabled={loading}
            >
              {loading ? "Signing in..." : "Sign In"}
            </button>
          </form>

          <p className="login-security-note">
            Authorized users only. Please keep your login credentials secure.
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;
