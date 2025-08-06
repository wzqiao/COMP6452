import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { API_BASE_URL } from "./config";
import {
  UploadCloud,
  ArrowLeft,
  CheckCircle,
  XCircle,
  AlertTriangle,
} from "lucide-react";

export default function InspectionDetailPage({ onLogout }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const token = localStorage.getItem("token");
  const [batchInfo, setBatchInfo] = useState(null);
  const [inspection, setInspection] = useState(null);
  const [file, setFile] = useState(null);
  const [notes, setNotes] = useState("");
  const [uploading, setUploading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  useEffect(() => {
    const fetchInspections = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/batches/${id}/inspections`, {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        const data = await res.json();
  
        if (!res.ok) throw new Error(data.error || "Failed to fetch inspection");
  
        setBatchInfo(data.batch);
        console.log(data)
        
        if (data.inspections && data.inspections.length > 0) {
          setInspection(data.inspections[0]);
          setNotes(data.inspections[0].notes || "");
        } else {
          setInspection(null);
          setNotes("");
        }
  
      } catch (err) {
        setError(err.message);
      }
    };
  
    fetchInspections();
  }, [id, token]);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type !== "application/pdf") {
      setError("Only PDF files are allowed.");
      setFile(null);
    } else {
      setError("");
      setFile(selectedFile);
    }
  };  

  console.log(token);
  const uploadPdfToExternal = async (pdfFile) => {
    const filename = pdfFile.name;
    console.log(token);
  
    const res = await fetch("https://wvdam1xz7a.execute-api.ap-southeast-2.amazonaws.com/default/UploadPdf_6452", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
      body: JSON.stringify({ filename }),
    });
  
    const data = await res.json();

    console.log(data);
    
    if (!res.ok) throw new Error(data.error || "Failed to upload PDF");

    const uploadUrl = data.url;

    console.log(uploadUrl);

    const uploadRes = await fetch(uploadUrl, {
      method: "PUT",
      body: pdfFile,
    });

    console.log(uploadRes);
  
    if (!uploadRes.ok) {
      throw new Error("Failed to upload PDF to S3");
    }

    const cleanUrl = data.public;
    return cleanUrl;
  };  

  const handleUpdate = async (result) => {
    setSubmitting(true);
    setError("");
    setSuccessMsg("");
  
    try {
      let fileUrl = inspection?.file_url || null;
  
      // Validate that a file must be uploaded for new inspections
      if (!fileUrl && !file) {
        setError("Please upload a PDF file before submitting the inspection result.");
        setSubmitting(false);
        return;
      }
  
      if (file) {
        setUploading(true);
        fileUrl = await uploadPdfToExternal(file);
      }
  
      const res = await fetch(`${API_BASE_URL}/batches/${id}/inspection`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          result,
          notes,  
          file_url: fileUrl,
        }),
      });
  
      const data = await res.json();
      
      // Check response status code
      if (!res.ok) {
        throw new Error(data.error || "Failed to submit inspection result");
      }
  
      setSuccessMsg("Update successfully!");
      setInspection(
        data.inspection || {
          ...inspection,
          result,
          notes,
          file_url: fileUrl,
        }
      );
      setFile(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
      setUploading(false);
    }
  };  
  

  if (!batchInfo) {
    return <div className="container py-5">Loading...</div>;
  }

  return (
    <div className="container py-5">
      <div
        className="position-absolute top-0 end-0 p-3 d-flex gap-2"
        style={{ zIndex: 10 }}
      >
        <button
          className="btn btn-outline-secondary"
          onClick={() => navigate(-1)}
        >
        <ArrowLeft className="me-2" size={16} />
          Back to the list
        </button>  
        <button className="btn btn-outline-secondary" onClick={onLogout}>
          logout
        </button>
      </div>
      <h3 className="fw-bold mb-4">Batch details</h3>
      <div className="card p-4 shadow-sm mb-4">
        <p><strong>Product name: </strong>{batchInfo.product_name}</p>
        <p><strong>Batch number: </strong>{batchInfo.batch_number}</p>
        <p><strong>Status: </strong>{batchInfo.status}</p>
      </div>
  
      <h4 className="fw-bold mb-3">the newest records</h4>
      {inspection ? (
        <div className="card p-4 shadow-sm mb-4">
          <p><strong>Inspector: </strong>{inspection.inspector_name}</p>
          <p><strong>Inspection time: </strong>{new Date(inspection.insp_date).toLocaleString()}</p>
          <p><strong>Result: </strong>{(inspection.result || "unknown").toUpperCase()}</p>
          <p><strong>Report link: </strong>
            {inspection.file_url ? (
              <a href={inspection.file_url} target="_blank" rel="noreferrer">
                Check PDF
              </a>
            ) : "No"}
          </p>
          <p><strong>Remark: </strong>{inspection.notes || "No"}</p>
        </div>
      ) : (
        <div className="alert alert-secondary">No inspection records</div>
      )}
  
      <div className="card p-4 shadow-sm mb-4">
        <h5>
          <UploadCloud className="me-2 text-primary" size={18} />
          Upload new report and update results
        </h5>
        <div className="mb-3">
          <label className="form-label">
            PDF Report <span className="text-danger">*</span>
            {!inspection?.file_url && (
              <small className="text-muted"> (Required for new inspections)</small>
            )}
          </label>
          <input
            type="file"
            className="form-control"
            accept="application/pdf"
            onChange={handleFileChange}
            disabled={uploading || submitting}
          />
          {file && (
            <small className="text-success">
              ✓ File selected: {file.name}
            </small>
          )}
        </div>
        <textarea
          className="form-control mb-3"
          rows={3}
          placeholder="Remark"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          disabled={uploading}
        />
        <button
          className="btn btn-primary mb-3"
          onClick={() => {
            if (!file && !notes) {
              setError("Please select a file or enter remarks.");
              return;
            }
            setInspection({ ...inspection, file_url: null, notes });
            setSuccessMsg("File selected and remark noted. Please submit a result to finalize.");
          }}
          disabled={uploading || submitting}
        >
          <UploadCloud className="me-1" size={18} />
          Confirm Upload
        </button>

        <div className="d-flex gap-3">
          <button
            className="btn btn-success"
            onClick={() => handleUpdate("passed")}
            disabled={submitting || uploading || (!inspection?.file_url && !file)}
            title={(!inspection?.file_url && !file) ? "Please upload a PDF file first" : ""}
          >
            <CheckCircle className="me-1" size={18} />
              Pass
          </button>
          <button
            className="btn btn-danger"
            onClick={() => handleUpdate("failed")}
            disabled={submitting || uploading || (!inspection?.file_url && !file)}
            title={(!inspection?.file_url && !file) ? "Please upload a PDF file first" : ""}
          >
            <XCircle className="me-1" size={18} />
              Failed
          </button>
          <button
            className="btn btn-warning text-dark"
            onClick={() => handleUpdate("needs_recheck")}
            disabled={submitting || uploading || (!inspection?.file_url && !file)}
            title={(!inspection?.file_url && !file) ? "Please upload a PDF file first" : ""}
          >
          <AlertTriangle className="me-1" size={18} />
            Need re-examination
          </button>
        </div>
      </div>

      {error && (
        <div className="alert alert-danger mt-3" role="alert">
          {error}
        </div>
      )}
      {successMsg && (
        <div className="alert alert-success mt-3" role="alert">
          {successMsg}
        </div>
      )}
    </div>
  );  
}