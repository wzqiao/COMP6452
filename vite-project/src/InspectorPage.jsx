import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

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
            `http://127.0.0.1:5000/batches?page=${page}&per_page=${perPage}`,
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
            console.warn("返回不是有效 JSON", text);
          }

          if (!res.ok) {
            throw new Error(data.message || `无法获取批次列表: ${res.status}`);
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

  // 根据筛选条件过滤
  const filteredBatches =
    filter === "all"
      ? batches
      : batches.filter((b) => b.status === filter);

  return (
    <div className="container py-4">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h2 className="mb-0">检验记录列表</h2>
        <button className="btn btn-outline-secondary" onClick={onLogout}>
          退出登录
        </button>
      </div>

      {/* 状态筛选下拉菜单 */}
      <div className="mb-3">
        <select
          className="form-select w-auto"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        >
          <option value="all">全部</option>
          <option value="pending">待检验</option>
          <option value="inspected">已检验</option>
          <option value="approved">通过</option>
          <option value="rejected">不通过</option>
        </select>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {filteredBatches.length === 0 ? (
        <p className="text-muted">暂无符合条件的检验记录</p>
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