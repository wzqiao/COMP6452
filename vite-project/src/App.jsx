import React, { useEffect, useState } from "react";
import { Routes, Route, useNavigate } from "react-router-dom";
import LoginRegister from "./LoginRegister";
import WalletBindModal from "./WalletBindModal";
import ProducerPage from "./ProducerPage";
import InspectorPage from "./InspectorPage";
import InspectionDetailPage from "./InspectionDetailPage";
import ConsumerPage from "./ConsumerPage";

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [role, setRole] = useState(localStorage.getItem("role"));
  const [walletBound, setWalletBound] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {

    if (location.pathname.startsWith("/batches/")) {
      return;
    }

    if (role === "consumer") {
      navigate("/consumer");
    } else if (role === "producer" && token && walletBound) {
      navigate("/producer");
    } else if (role === "inspector" && token && walletBound) {
      navigate("/inspector");
    }
  }, [role, token, walletBound, navigate]);

  const handleAuthSuccess = (token) => {
    setToken(token);
    if (token) localStorage.setItem("token", token);

    // 如果是 Consumer，不需要绑定钱包
    if (role === "consumer") {
      navigate("/consumer");
    }
  };

  const handleSetRole = (r) => {
    setRole(r);
    localStorage.setItem("role", r);
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    setToken(null);
    setRole(null);
    setWalletBound(false);
    navigate("/"); // 回到首页
  };

  return (
    <>
      {/* 钱包绑定弹窗（只针对 Producer/Inspector） */}
      {token && role !== "consumer" && !walletBound && (
        <WalletBindModal
          token={token}
          onBindSuccess={() => {
            setWalletBound(true);
          }}
        />
      )}

      <Routes>
        <Route
          path="/"
          element={
            <LoginRegister onAuthSuccess={handleAuthSuccess} setRole={handleSetRole} />
          }
        />
        <Route path="/consumer" element={<ConsumerPage onLogout={logout} />} />
        <Route path="/producer" element={<ProducerPage onLogout={logout} />} />
        <Route path="/inspector" element={<InspectorPage onLogout={logout} />} />
        <Route path="/batches/:id/inspections" element={<InspectionDetailPage onLogout={logout} />} />
      </Routes>
    </>
  );
}