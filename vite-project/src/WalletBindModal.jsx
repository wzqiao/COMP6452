import React, { useEffect, useState, useCallback } from "react";

export default function WalletBindModal({ token, onBindSuccess }) {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [isVisible, setIsVisible] = useState(true);

  const requestWallet = useCallback(async () => {
    setError("");
    setLoading(true);

    if (!window.ethereum) {
      setError("请安装MetaMask钱包插件");
      setLoading(false);
      return;
    }

    try {
      const accounts = await window.ethereum.request({
        method: "eth_requestAccounts",
      });
      if (!accounts || accounts.length === 0) {
        throw new Error("未获取到钱包地址");
      }

      const walletAddress = accounts[0];

      const res = await fetch("http://127.0.0.1:5000/auth/wallet", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ wallet: walletAddress }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.message || "绑定失败");

      setIsVisible(false);
      onBindSuccess();
    } catch (e) {
      setError(e.message || "绑定失败");
    } finally {
      setLoading(false);
    }
  }, [token, onBindSuccess]);

  useEffect(() => {
    requestWallet();
  }, [requestWallet]);

  if (!isVisible) return null;

  return (
    <div
      className="modal d-block"
      tabIndex="-1"
      style={{ backgroundColor: "rgba(0,0,0,0.5)" }}
    >
      <div
        className="modal-dialog modal-dialog-centered"
        role="document"
        style={{ maxWidth: 400 }}
      >
        <div className="modal-content p-4 position-relative">
          {/* 关闭按钮 */}
          <button
            type="button"
            className="btn-close position-absolute top-0 end-0 m-3"
            aria-label="Close"
            onClick={() => setIsVisible(false)}
          ></button>

          <h5 className="modal-title mb-3">绑定您的MetaMask钱包</h5>

          {loading && <p>请求钱包授权中，请在弹窗中确认...</p>}

          {error && (
            <div className="alert alert-danger">
              {error}
              <br />
              您可以点击下方按钮重新尝试绑定。
            </div>
          )}

          {!loading && (
            <button
              className="btn btn-primary mt-3"
              onClick={() => requestWallet()}
            >
              重新尝试绑定
            </button>
          )}

          <p className="mt-3 text-muted" style={{ fontSize: "0.85rem" }}>
            绑定钱包后，才能继续上传文件和使用系统功能。
          </p>
        </div>
      </div>
    </div>
  );
}