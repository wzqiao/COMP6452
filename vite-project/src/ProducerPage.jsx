import React, { useState } from "react";
import { CheckCircle, PlusCircle } from "lucide-react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { parseISO } from "date-fns";

export default function ProducerPage({ onLogout }) {
  const [form, setForm] = useState({
    batchNumber: "",
    productName: "",
    origin: "",
    quantity: "",
    unit: "",
    harvestDate: "",
    expiryDate: "",
    organic: false,
    import: false,
  });

  const [submittedBatch, setSubmittedBatch] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm({
      ...form,
      [name]: type === "checkbox" ? checked : value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);

    const token = localStorage.getItem("token");
    if (!token) {
      setError("未登录，无法提交");
      setSubmitting(false);
      return;
    }

    const payload = {
      metadata: {
        ...form,
        harvestDate: form.harvestDate || null,
        expiryDate: form.expiryDate || null,
      },
    };

    try {
      const res = await fetch("http://127.0.0.1:5000/batches", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      const text = await res.text();
      let data = {};
      try {
        data = text ? JSON.parse(text) : {};
      } catch {
        console.warn("返回不是有效 JSON", text);
      }

      if (!res.ok) {
        throw new Error(data.message || `提交失败: ${res.status}`);
      }

      setSubmittedBatch(data);
      console.log("后端返回的数据:", data);

      setForm({
        batchNumber: "",
        productName: "",
        origin: "",
        quantity: "",
        unit: "",
        harvestDate: "",
        expiryDate: "",
        organic: false,
        import: false,
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container py-5">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2 className="fw-bold">Create new batch(Producer)</h2>
        <button className="btn btn-outline-secondary" onClick={onLogout}>
          Logout
        </button>
      </div>

      <div className="card shadow-sm p-4">
        <h5 className="mb-3">
          <PlusCircle size={18} className="me-2 text-primary" />
          Fill in batch information
        </h5>

        <form onSubmit={handleSubmit}>
          {/* 文本字段 */}
          {["batchNumber", "productName", "origin", "quantity", "unit"].map(
            (field) => (
              <div className="mb-3" key={field}>
                <label className="form-label">{field}</label>
                <input
                  type="text"
                  className="form-control"
                  name={field}
                  value={form[field]}
                  onChange={handleChange}
                  required
                />
              </div>
            )
          )}

          {/* 日期字段 */}
          {["harvestDate", "expiryDate"].map((field) => (
            <div className="mb-3" key={field}>
            <label className="form-label">{field}</label>
            <DatePicker
              className="form-control"
              selected={form[field] ? new Date(form[field]) : null}
              onChange={(date) =>
              setForm({ ...form, [field]: date.toISOString().split("T")[0] })
              }
              dateFormat="dd/MM/yyyy"
              placeholderText="dd/mm/yyyy"
            />
          </div>
          ))}

          {/* 有机 & 进口 */}
          <div className="form-check mb-2">
            <input
              className="form-check-input"
              type="checkbox"
              name="organic"
              id="organic"
              checked={form.organic}
              onChange={handleChange}
            />
            <label className="form-check-label" htmlFor="organic">
              是否为有机产品
            </label>
          </div>

          <div className="form-check mb-3">
            <input
              className="form-check-input"
              type="checkbox"
              name="import"
              id="import"
              checked={form.import}
              onChange={handleChange}
            />
            <label className="form-check-label" htmlFor="import">
              是否为进口产品
            </label>
          </div>

          {error && <div className="alert alert-danger">{error}</div>}

          <button
            type="submit"
            className="btn btn-primary w-100"
            disabled={submitting}
          >
            {submitting ? "提交中..." : "提交批次信息并上链"}
          </button>
        </form>
      </div>

      {submittedBatch && (
        <div className="alert alert-success mt-4">
          <CheckCircle className="me-2" size={20} />
          批次 <strong>{submittedBatch.batchNumber || "未知"}</strong> 已成功提交！
        </div>
      )}
    </div>
  );
}