import React, { useEffect, useState } from "react";
import { API_BASE_URL } from "./config";

export default function ConsumerPage({ onLogout }) {
  const [batches, setBatches] = useState([]);
  const [filteredBatches, setFilteredBatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [searchId, setSearchId] = useState("");
  const [filterResult, setFilterResult] = useState("");
  const [filterOrganic, setFilterOrganic] = useState("");
  const [filterImport, setFilterImport] = useState("");

  // Timestamp conversion function
  const formatDate = (timestamp) => {
    if (!timestamp) return "N/A";
    try {
      return new Date(timestamp * 1000).toLocaleDateString();
    } catch (error) {
      return "Invalid Date";
    }
  };

  useEffect(() => {
    const fetchBatches = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/batches?per_page=1000`);
        const data = await res.json();
        console.log("Fetched batches:", data.batches);

        if (!res.ok) throw new Error(data.error || "Failed to fetch batches");
        setBatches(data.batches || []);
        setFilteredBatches(data.batches || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchBatches();
  }, []);

  useEffect(() => {
    let filtered = [...batches];

    // Search by batch ID
    if (searchId.trim()) {
      filtered = filtered.filter((b) =>
        b.batchId.toString().includes(searchId.trim())
      );
    }

    // Filter by status
    if (filterResult) {
      filtered = filtered.filter((b) => {
        const status = b.status || "unknown";
        return status === filterResult;
      });
    }

    // Filter by organic standard
    if (filterOrganic) {
      filtered = filtered.filter(
        (b) => String(b.metadata?.organic) === filterOrganic
      );
    }

    // Filter by import standard
    if (filterImport) {
      filtered = filtered.filter(
        (b) => String(b.metadata?.import) === filterImport
      );
    }

    setFilteredBatches(filtered);
  }, [searchId, filterResult, filterOrganic, filterImport, batches]);

  return (
    <div className="container py-5">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2 className="fw-bold">Batch Viewer (Consumer)</h2>
        <button className="btn btn-outline-secondary" onClick={onLogout}>
          Logout
        </button>
      </div>

      {/* Search and filter */}
      <div className="row mb-4">
        <div className="col-md-3 mb-2">
          <input
            type="text"
            className="form-control"
            placeholder="Search by Batch ID"
            value={searchId}
            onChange={(e) => setSearchId(e.target.value)}
          />
        </div>
        <div className="col-md-3 mb-2">
          <select
            className="form-select"
            value={filterResult}
            onChange={(e) => setFilterResult(e.target.value)}
          >
            <option value="">All Status</option>
            <option value="approved">approved</option>
            <option value="rejected">rejected</option>
            <option value="pending">pending</option>
            <option value="inspected">inspected</option>
          </select>
        </div>
        <div className="col-md-3 mb-2">
          <select
            className="form-select"
            value={filterOrganic}
            onChange={(e) => setFilterOrganic(e.target.value)}
          >
            <option value="">All Organic</option>
            <option value="true">true</option>
            <option value="false">false</option>
          </select>
        </div>
        <div className="col-md-3 mb-2">
          <select
            className="form-select"
            value={filterImport}
            onChange={(e) => setFilterImport(e.target.value)}
          >
            <option value="">All Import</option>
            <option value="true">true</option>
            <option value="false">false</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="text-center my-5">
          <div className="spinner-border text-primary" role="status" />
          <div className="mt-3">Loading...</div>
        </div>
      ) : error ? (
        <div className="alert alert-danger">{error}</div>
      ) : (
        <div className="table-responsive">
          <table className="table table-bordered table-hover align-middle">
            <thead className="table-light">
              <tr>
                <th>Batch ID</th>
                <th>Product Name</th>
                <th>Status</th>
                <th>File URL</th>
                <th>Blockchain TX</th>
                <th>Organic</th>
                <th>Import</th>
                <th>Harvest Date</th>
                <th>Expiry Date</th>
              </tr>
            </thead>
            <tbody>
              {filteredBatches.map((batch) => {
                const metadata = batch.metadata || {};

                return (
                  <tr key={batch.batchId}>
                    <td>{batch.batchId}</td>
                    <td>{metadata.productName || "N/A"}</td>

                    {/* Status */}
                    <td>
                      <span
                        className={`badge ${
                          batch.status === "approved"
                            ? "bg-success"
                            : batch.status === "rejected"
                            ? "bg-danger"
                            : batch.status === "pending"
                            ? "bg-warning"
                            : "bg-secondary"
                        }`}
                      >
                        {batch.status || "unknown"}
                      </span>
                    </td>

                    {/* File URL */}
                    <td>
                      {batch.fileUrl && batch.fileUrl !== "none" ? (
                        <a
                          href={batch.fileUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-decoration-none"
                        >
                          {batch.fileUrl}
                        </a>
                      ) : (
                        <span className="text-muted">none</span>
                      )}
                    </td>

                    {/* Blockchain TX */}
                    <td
                      className="font-monospace text-break"
                      style={{ maxWidth: "200px" }}
                    >
                      {batch.blockchainTx ? (
                        <small>{batch.blockchainTx}</small>
                      ) : (
                        <span className="text-muted">none</span>
                      )}
                    </td>

                    {/* Organic */}
                    <td>
                      <span
                        className={`badge ${
                          metadata.organic ? "bg-success" : "bg-secondary"
                        }`}
                      >
                        {String(metadata.organic)}
                      </span>
                    </td>

                    {/* Import */}
                    <td>
                      <span
                        className={`badge ${
                          metadata.import ? "bg-info" : "bg-secondary"
                        }`}
                      >
                        {String(metadata.import)}
                      </span>
                    </td>

                    {/* Harvest Date */}
                    <td>{formatDate(metadata.harvestDate)}</td>

                    {/* Expiry Date */}
                    <td>{formatDate(metadata.expiryDate)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {filteredBatches.length === 0 && (
            <div className="text-center text-muted py-4">
              No matching batches found.
            </div>
          )}
        </div>
      )}

      {/* Data statistics */}
      {!loading && !error && (
        <div className="mt-3 text-muted small">
          Showing {filteredBatches.length} of {batches.length} batches from
          blockchain
          {filteredBatches.length !== batches.length && ` (filtered)`}
        </div>
      )}
    </div>
  );
}
