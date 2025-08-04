import React, { useState } from "react";
import { Mail, Lock } from "lucide-react";
import { API_BASE_URL } from "./config";

export default function LoginRegister({ onAuthSuccess, setRole }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [role, setSelectedRole] = useState("");
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  const roleOptions = isLogin
    ? ["producer", "inspector", "consumer"]
    : ["producer", "inspector"];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccessMsg("");

    if (!role) {
      setError("Please select a role");
      return;
    }

    if (role === "consumer") {
      setRole("consumer");
      onAuthSuccess(null);
      return;
    }

    if (!email || !password) {
      setError("Please enter email and password");
      return;
    }

    if (!isLogin && password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    const url = isLogin ? `${API_BASE_URL}/auth/login` : `${API_BASE_URL}/auth/register`;
    const body = isLogin ? { email, password } : { email, password, role };

    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      const text = await res.text();

      let data = {};
      try {
        data = text ? JSON.parse(text) : {};
      } catch (e) {
        console.warn("Not a valid JSON", text);
      }

      if (!res.ok) {
        throw new Error(data?.message || data?.msg || `Request failed: ${res.status}`);
      }

      if (isLogin) {
        localStorage.setItem("token", data.token);
        localStorage.setItem("role", data.role);
        setRole(data.role);
        onAuthSuccess(data.token);
      } else {
        console.log(data);
        setSuccessMsg("Registration successful, please login");
        setIsLogin(true);
        setEmail("");
        setPassword("");
        setConfirmPassword("");
        setSelectedRole("");
      }
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="container d-flex justify-content-center align-items-center min-vh-100">
      <div className="card shadow-lg p-4" style={{ width: "100%", maxWidth: 480 }}>
        <h3 className="text-center mb-4">{isLogin ? "Login" : "Register"}</h3>
        <form onSubmit={handleSubmit}>
          {role !== "consumer" && (
            <>
              <div className="mb-3">
                <label className="form-label">Email</label>
                <div className="input-group">
                  <span className="input-group-text">
                    <Mail size={18} />
                  </span>
                  <input
                    type="email"
                    className="form-control"
                    placeholder="example@email.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
              </div>

              <div className="mb-3">
                <label className="form-label">Password</label>
                <div className="input-group">
                  <span className="input-group-text">
                    <Lock size={18} />
                  </span>
                  <input
                    type="password"
                    className="form-control"
                    placeholder="Enter password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </div>
              </div>

              {!isLogin && (
                <div className="mb-3">
                  <label className="form-label">Confirm password</label>
                  <div className="input-group">
                    <span className="input-group-text">
                      <Lock size={18} />
                    </span>
                    <input
                      type="password"
                      className="form-control"
                      placeholder="Enter password again"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                    />
                  </div>
                </div>
              )}
            </>
          )}

          <div className="mb-3">
            <label className="form-label">Role</label>
            {roleOptions.map((opt) => (
              <div className="form-check" key={opt}>
                <input
                  className="form-check-input"
                  type="radio"
                  name="role"
                  id={`role-${opt}`}
                  value={opt}
                  checked={role === opt}
                  onChange={() => setSelectedRole(opt)}
                />
                <label className="form-check-label" htmlFor={`role-${opt}`}>
                  {opt}
                </label>
              </div>
            ))}
          </div>

          {error && <div className="alert alert-danger">{error}</div>}
          {successMsg && <div className="alert alert-success">{successMsg}</div>}

          <button type="submit" className="btn btn-primary w-100">
            {isLogin ? "Login" : "Register"}
          </button>
        </form>

        <div className="text-center mt-3">
          {isLogin ? (
            <small>
              No account?{" "}
              <button className="btn btn-link p-0" onClick={() => setIsLogin(false)}>
                Register
              </button>
            </small>
          ) : (
            <small>
              Have an account?{" "}
              <button className="btn btn-link p-0" onClick={() => setIsLogin(true)}>
                Login
              </button>
            </small>
          )}
        </div>
      </div>
    </div>
  );
}