import React, { useState } from "react";
import { Mail, Lock } from "lucide-react";

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
      setError("请选择身份");
      return;
    }

    if (role === "consumer") {
      setRole("consumer");
      onAuthSuccess(null);
      return;
    }

    if (!email || !password) {
      setError("请填写邮箱和密码");
      return;
    }

    if (!isLogin && password !== confirmPassword) {
      setError("两次密码不一致");
      return;
    }

    const url = isLogin ? "http://127.0.0.1:5000/auth/login" : "http://127.0.0.1:5000/auth/register";
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
        console.warn("返回不是有效 JSON", text);
      }

      if (!res.ok) {
        throw new Error(data?.message || data?.msg || `请求失败: ${res.status}`);
      }

      if (isLogin) {
        localStorage.setItem("token", data.token);
        localStorage.setItem("role", data.role);
        setRole(data.role);
        onAuthSuccess(data.token);
      } else {
        console.log(data);
        setSuccessMsg("注册成功，请登录");
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
        <h3 className="text-center mb-4">{isLogin ? "登录" : "注册"}</h3>
        <form onSubmit={handleSubmit}>
          {role !== "consumer" && (
            <>
              <div className="mb-3">
                <label className="form-label">邮箱</label>
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
                <label className="form-label">密码</label>
                <div className="input-group">
                  <span className="input-group-text">
                    <Lock size={18} />
                  </span>
                  <input
                    type="password"
                    className="form-control"
                    placeholder="请输入密码"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </div>
              </div>

              {!isLogin && (
                <div className="mb-3">
                  <label className="form-label">确认密码</label>
                  <div className="input-group">
                    <span className="input-group-text">
                      <Lock size={18} />
                    </span>
                    <input
                      type="password"
                      className="form-control"
                      placeholder="再次输入密码"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                    />
                  </div>
                </div>
              )}
            </>
          )}

          <div className="mb-3">
            <label className="form-label">身份选择</label>
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
            {isLogin ? "登录" : "注册"}
          </button>
        </form>

        <div className="text-center mt-3">
          {isLogin ? (
            <small>
              没有账号？{" "}
              <button className="btn btn-link p-0" onClick={() => setIsLogin(false)}>
                去注册
              </button>
            </small>
          ) : (
            <small>
              已有账号？{" "}
              <button className="btn btn-link p-0" onClick={() => setIsLogin(true)}>
                去登录
              </button>
            </small>
          )}
        </div>
      </div>
    </div>
  );
}