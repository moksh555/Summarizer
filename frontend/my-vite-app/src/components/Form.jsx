import React, { useRef, useState } from "react";
import axios from "axios";
import "./Form.css"; // <-- add this

export default function Form() {
  const fileRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");
  const API_URL = `${BASE}/summaries`;

  const onSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setProgress(0);
    setError(null);
    setResult(null);

    const file = fileRef.current?.files?.[0];
    if (!file) {
      setLoading(false);
      setProgress(null);
      setError("Please choose a PDF file.");
      return;
    }

    const fd = new FormData();
    fd.append("file", file);

    try {
      const res = await axios.post(API_URL, fd, {
        headers: { Accept: "application/json" },
        onUploadProgress: (evt) => {
          if (evt.total)
            setProgress(Math.round((evt.loaded * 100) / evt.total));
        },
        validateStatus: () => true,
        timeout: 120000,
      });

      const payload = res.data;
      const isSuccess =
        payload?.status === true ||
        (typeof payload?.status === "string" &&
          payload.status.toLowerCase().startsWith("suc"));

      if (!isSuccess || res.status < 200 || res.status >= 300) {
        throw new Error(
          payload?.message || `Request failed (HTTP ${res.status}).`
        );
      }

      setResult(payload);
    } catch (err) {
      setError(err.message || "Upload failed.");
    } finally {
      setLoading(false);
      setProgress(null);
    }
  };

  const docUrl = result?.documentId
    ? `https://docs.google.com/document/d/${result.documentId}/edit`
    : null;

  return (
    <div className="form-wrap">
      <form className="card" onSubmit={onSubmit}>
        <h1 className="title">PDF Summarizer</h1>

        <label htmlFor="file" className="label">
          Please upload your PDF here
        </label>

        <input
          id="file"
          type="file"
          name="file"
          accept="application/pdf"
          required
          ref={fileRef}
          className="file-input"
        />

        <button type="submit" className="btn" disabled={loading}>
          {loading ? "Summarizing…" : "Summarize"}
        </button>

        {progress !== null && (
          <div
            className="progress"
            role="progressbar"
            aria-valuenow={progress}
            aria-valuemin="0"
            aria-valuemax="100"
          >
            <div className="bar" style={{ width: `${progress}%` }} />
            <span className="pct">{progress}%</span>
          </div>
        )}

        {error && (
          <p className="error" role="alert" aria-live="polite">
            {error}
          </p>
        )}
      </form>

      {result && (
        <div className="result card">
          <p className="muted">Created</p>
          <h2 className="doc-name">{result.fileName}</h2>
          {docUrl && (
            <p className="link-row">
              <a
                className="link"
                href={docUrl}
                target="_blank"
                rel="noreferrer"
              >
                Open Google Doc
              </a>
            </p>
          )}

          <details className="details">
            <summary>Raw JSON response</summary>
            <pre className="pre">{JSON.stringify(result, null, 2)}</pre>
          </details>
        </div>
      )}
    </div>
  );
}
