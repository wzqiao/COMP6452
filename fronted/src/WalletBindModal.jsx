import React, { useEffect, useState, useCallback } from "react";
import { API_BASE_URL } from "./config";

export default function WalletBindModal({ token, onBindSuccess }) {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [isVisible, setIsVisible] = useState(true);

  const requestWallet = useCallback(async () => {
    setError("");
    setLoading(true);

    if (!window.ethereum) {
      setError("Please install MetaMask wallet plugin");
      setLoading(false);
      return;
    }

    try {
      const accounts = await window.ethereum.request({
        method: "eth_requestAccounts",
      });
      if (!accounts || accounts.length === 0) {
        throw new Error("Wallet address not found");
      }

      const walletAddress = accounts[0];

      const res = await fetch(`${API_BASE_URL}/auth/wallet`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ wallet: walletAddress }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.message || "Binding failed");

      setIsVisible(false);
      onBindSuccess();
    } catch (e) {
      setError(e.message || "Binding failed");
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
          {/* Close button */}
          <button
            type="button"
            className="btn-close position-absolute top-0 end-0 m-3"
            aria-label="Close"
            onClick={() => setIsVisible(false)}
          ></button>

          <h5 className="modal-title mb-3">Bind your MetaMask wallet</h5>

          {loading && <p>Requesting wallet authorization, please confirm in the popup...</p>}

          {error && (
            <div className="alert alert-danger">
              {error}
              <br />
              You can click the button below to try binding again.
            </div>
          )}

          {!loading && (
            <button
              className="btn btn-primary mt-3"
              onClick={() => requestWallet()}
            >
              Try binding again
            </button>
          )}

          <p className="mt-3 text-muted" style={{ fontSize: "0.85rem" }}>
            After binding the wallet, you can continue to upload files and use system functions.
          </p>
        </div>
      </div>
    </div>
  );
}