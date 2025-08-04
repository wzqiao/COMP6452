import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { API_BASE_URL } from "./config";

export default function InspectorPage({ onLogout }) {
  const [batches, setBatches] = useState([]);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("all");
  const token = localStorage.getItem("token");
  const navigate = useNavigate();

  useEffect(() => {
    const fetchAllBatches = async () => {
      let allBatches = [];
      let page = 1;
      const perPage = 20;

      try {
        while (true) {
          const res = await fetch(
            `${API_BASE_URL}/batches?page=${page}&per_page=${perPage}`,
            {
              method: "GET",
              headers: { Authorization: `Bearer ${token}` },
            }
          );

          const text = await res.text();
          let data = {};
          try {
            data = text ? JSON.parse(text) : {};
          } catch {
            console.warn("Not a valid JSON", text);
          }

          if (!res.ok) {
            throw new Error(data.message || `Failed to get batch list: ${res.status}`);
          }

          const batchesPage = data.batches || [];
          allBatches = allBatches.concat(batchesPage);

          if (batchesPage.length < perPage) break;
          page++;
        }

        setBatches(allBatches);
      } catch (err) {
        setError(err.message);
      }
    };

    fetchAllBatches();
  }, [token]);

  // Filter by filter condition
  const filteredBatches =
    filter === "all"
      ? batches
      : batches.filter((b) => b.status === filter);

  return (
    <div className="container py-4">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h2 className="mb-0">Inspection record list</h2>
        <button className="btn btn-outline-secondary" onClick={onLogout}>
          Logout
        </button>
      </div>

      {/* Status filter dropdown menu */}
      <div className="mb-3">
        <select
          className="form-select w-auto"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        >
          <option value="all">All</option>
          <option value="pending">Pending</option>
          <option value="inspected">Inspected</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {filteredBatches.length === 0 ? (
        <p className="text-muted">No inspection records found</p>
      ) : (
        <ul className="list-group">
          {filteredBatches.map((insp) => (
            <li
              key={insp.batchId}
              className="list-group-item list-group-item-action"
              onClick={() =>
                navigate(`/batches/${insp.batchId}/inspections`)
              }
              style={{ cursor: "pointer" }}
            >
              {insp.metadata.batchNumber} - {insp.metadata.productName} -{" "}
              {insp.status}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}