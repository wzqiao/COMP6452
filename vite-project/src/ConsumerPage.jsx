import React, { useEffect, useState } from "react";

export default function ConsumerPage({ onLogout }) {
  const [batches, setBatches] = useState([]);
  const [filteredBatches, setFilteredBatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [searchId, setSearchId] = useState("");
  const [filterResult, setFilterResult] = useState("");
  const [filterOrganic, setFilterOrganic] = useState("");
  const [filterImport, setFilterImport] = useState("");

  useEffect(() => {
    const fetchBatches = async () => {
      try {
        const res = await fetch("http://127.0.0.1:5000/batches?per_page=1000");
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
  
    if (searchId.trim()) {
      filtered = filtered.filter((b) =>
        b.batchId.toString().includes(searchId.trim())
      );
    }
  
    if (filterResult) {
      filtered = filtered.filter((b) => {
        const result = b.inspections?.[0]?.result || "none";
        return result === filterResult;
      });
    }
  
    if (filterOrganic) {
      filtered = filtered.filter(
        (b) => String(b.metadata?.organic) === filterOrganic
      );
    }
  
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

      {/* 搜索和筛选器 */}
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
            <option value="">All Results</option>
            <option value="passed">passed</option>
            <option value="failed">failed</option>
            <option value="needs_recheck">needs_recheck</option>
            <option value="none">none</option>
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
                <th>Result</th>
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
                const firstInspection = batch.inspections?.[0];
                const metadata = batch.metadata || {};

                return (
                  <tr key={batch.batchId}>
                    <td>{batch.batchId}</td>
                    <td>{metadata.productName || "N/A"}</td>
                    <td>{firstInspection?.result || "none"}</td>
                    <td>
                      {firstInspection?.fileUrl ? (
                        <a
                          href={firstInspection.fileUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          {firstInspection.fileUrl}
                        </a>
                      ) : (
                        "none"
                      )}
                    </td>
                    <td className="font-monospace text-break">
                      {batch.blockchainTx || "none"}
                    </td>
                    <td>{String(metadata.organic)}</td>
                    <td>{String(metadata.import)}</td>
                    <td>{metadata.harvestDate || "N/A"}</td>
                    <td>{metadata.expiryDate || "N/A"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {filteredBatches.length === 0 && (
            <div className="text-muted">No matching batches found.</div>
          )}
        </div>
      )}
    </div>
  );
}