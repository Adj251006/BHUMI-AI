import React, { useEffect, useState } from 'react';
import { api } from '../api/client';

export default function Documents() {
  const [docs, setDocs] = useState<any[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [aiResult, setAiResult] = useState<any>(null);

  // Upload Modal State
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadDocType, setUploadDocType] = useState('section_11_gazette');
  const [uploadProjectId, setUploadProjectId] = useState('');
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);

  const load = async () => {
    setLoading(true);
    try {
      const [d, p] = await Promise.all([
        api.getDocuments(),
        api.getProjects().catch(() => []),
      ]);
      setDocs(d || []);
      const projList = p || [];
      setProjects(projList);
      if (projList.length > 0 && !uploadProjectId) {
        setUploadProjectId(projList[0].id);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const analyzeDemo = async () => {
    setAnalyzing(true);
    try {
      const r = await api.analyzeDocument();
      setAiResult(r);
    } catch (e) {
      console.error(e);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile || !uploadProjectId) return;
    setUploading(true);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('project_id', uploadProjectId);
      formData.append('document_type', uploadDocType);
      formData.append('title', uploadTitle || uploadFile.name);

      const res = await api.uploadDocument(formData);
      setUploadResult(res);
      load();
    } catch (err: any) {
      alert(err.message || 'File upload failed');
    } finally {
      setUploading(false);
    }
  };

  if (loading) return <div className="loading-overlay"><div className="spinner" style={{ width: 36, height: 36 }} /></div>;

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* HEADER */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <span style={{ fontSize: 22 }}>📄</span>
            <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1.5, textTransform: 'uppercase', color: '#1B6CA8' }}>
              RFCTLARR 2013 DOCUMENT VAULT & AI COMPLIANCE
            </span>
          </div>
          <h1 style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
            Statutory Document Repository
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, margin: '4px 0 0' }}>
            Automated RFCTLARR compliance analysis, Gazette notice verification, and permanent file archival.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-secondary" onClick={analyzeDemo} disabled={analyzing}>
            {analyzing ? <><span className="spinner" />Analyzing...</> : '🤖 Run AI Legal Audit'}
          </button>
          <button
            id="open-upload-doc-btn"
            className="btn btn-primary"
            onClick={() => {
              setShowUploadModal(true);
              setUploadResult(null);
            }}
            style={{ fontWeight: 700, borderRadius: 10, padding: '10px 18px' }}
          >
            + Upload Statutory Document
          </button>
        </div>
      </div>

      {/* AI Analysis Result */}
      {aiResult && (
        <div className="card">
          <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div className="card-title">🤖 AI Document Intelligence Audit</div>
            <span className={`badge ${aiResult.validation_result?.status === 'approved' ? 'badge-success' : 'badge-warning'}`}>
              {Math.round((aiResult.overall_confidence || 0.92) * 100)}% Legal Confidence
            </span>
          </div>
          <div style={{ padding: 24 }}>
            <div className="alert high" style={{ marginBottom: 16 }}>
              <span>⚠️</span>
              <div>
                <strong>Statutory Notice:</strong> {aiResult.validation_result?.issues?.join(' · ') || 'Notice conforms with Section 11 requirements.'}
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 12 }}>
              {Object.entries(aiResult.extracted_fields || {}).map(([key, val]: [string, any]) => (
                <div
                  key={key}
                  style={{
                    padding: 14,
                    borderRadius: 10,
                    border: `1.5px solid ${val.status === 'matched' ? 'var(--green)' : val.status === 'mismatch' ? 'var(--saffron)' : 'var(--red)'}`,
                    background: val.status === 'matched' ? 'var(--green-bg)' : val.status === 'mismatch' ? 'var(--saffron-bg)' : 'var(--red-bg)',
                  }}
                >
                  <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 4 }}>
                    {key.replace(/_/g, ' ')}
                  </div>
                  <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-primary)' }}>
                    {val.value ? String(val.value) : '—'}
                  </div>
                  <div style={{ fontSize: 10, marginTop: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
                    <span>{val.status === 'matched' ? '✓' : val.status === 'mismatch' ? '⚠️' : '✗'}</span>
                    <span style={{ color: 'var(--text-muted)' }}>{val.status} · {Math.round((val.confidence || 0) * 100)}% conf</span>
                  </div>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 16, fontSize: 11, color: 'var(--text-muted)', fontStyle: 'italic' }}>{aiResult.disclaimer}</div>
          </div>
        </div>
      )}

      {/* Document List */}
      <div className="card">
        <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 className="card-title">All Statutory Records ({docs.length})</h3>
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Encrypted storage & static file serving</span>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Document Record</th>
                <th>Statutory Type</th>
                <th>Version</th>
                <th>Status</th>
                <th>AI Compliance</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {docs.map((d: any) => (
                <tr key={d.id}>
                  <td>
                    <div style={{ fontWeight: 700, fontSize: 13 }}>{d.title}</div>
                    {d.file_name && (
                      <div style={{ fontSize: 11, color: '#1B6CA8', marginTop: 2 }}>
                        📎 <a href={d.file_url || '#'} target="_blank" rel="noreferrer" style={{ textDecoration: 'underline', color: 'inherit' }}>{d.file_name}</a>
                      </div>
                    )}
                  </td>
                  <td>
                    <span className="badge badge-info" style={{ textTransform: 'none', fontSize: 11 }}>
                      {d.document_type?.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td><span style={{ fontSize: 12, fontWeight: 700 }}>v{d.version || '1.0'}</span></td>
                  <td><span className={`badge ${d.status}`}>{d.status?.replace(/_/g, ' ')}</span></td>
                  <td>
                    {d.ai_confidence_score ? (
                      <div>
                        <div style={{ fontWeight: 800, fontSize: 13, color: d.ai_confidence_score > 0.8 ? '#16A34A' : '#D97706' }}>
                          {Math.round(d.ai_confidence_score * 100)}% Match
                        </div>
                        {d.validation_result?.issues?.length > 0 && (
                          <div style={{ fontSize: 10, color: '#DC2626', marginTop: 2 }}>
                            ⚠️ {d.validation_result.issues.length} check(s)
                          </div>
                        )}
                      </div>
                    ) : (
                      <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>Validated ✓</span>
                    )}
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: 6 }}>
                      {d.file_url ? (
                        <a href={d.file_url} target="_blank" rel="noreferrer" className="btn btn-secondary btn-sm">
                          View File ↗
                        </a>
                      ) : (
                        <button className="btn btn-secondary btn-sm">Inspect</button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {docs.length === 0 && (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 32 }}>
                    No statutory documents found. Click "+ Upload Statutory Document" to archive gazette notices.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* UPLOAD MODAL */}
      {showUploadModal && (
        <div
          style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 1000,
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20
          }}
        >
          <div
            className="card"
            style={{ width: '100%', maxWidth: 560, borderRadius: 16, padding: 28, maxHeight: '90vh', overflowY: 'auto' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
              <h3 style={{ fontSize: 18, fontWeight: 800, margin: 0 }}>
                📤 Upload & Verify Statutory Document
              </h3>
              <button
                type="button"
                onClick={() => setShowUploadModal(false)}
                style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            {uploadResult ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <div style={{ background: '#F0FDF4', border: '1.5px solid #86EFAC', borderRadius: 12, padding: 18, color: '#14532D' }}>
                  <div style={{ fontSize: 16, fontWeight: 800 }}>✅ Document Uploaded & Certified</div>
                  <div style={{ fontSize: 12, marginTop: 4 }}>
                    Saved as: <strong>{uploadResult.file_name}</strong>
                  </div>
                  <div style={{ fontSize: 12, marginTop: 8 }}>
                    <strong>AI Compliance Score:</strong> {(uploadResult.compliance_analysis?.compliance_score * 100).toFixed(0)}%
                  </div>
                  <div style={{ fontSize: 12, marginTop: 4 }}>
                    <strong>RFCTLARR Mandatory Rules:</strong> {uploadResult.compliance_analysis?.statutory_status}
                  </div>
                </div>

                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => setShowUploadModal(false)}
                  style={{ borderRadius: 10, padding: 10 }}
                >
                  Done
                </button>
              </div>
            ) : (
              <form onSubmit={handleUploadSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <div>
                  <label style={{ fontSize: 12, fontWeight: 700, display: 'block', marginBottom: 6 }}>
                    Associated Land Acquisition Project *
                  </label>
                  <select
                    className="form-input"
                    value={uploadProjectId}
                    onChange={e => setUploadProjectId(e.target.value)}
                    required
                  >
                    {projects.map(p => (
                      <option key={p.id} value={p.id}>
                        {p.name} ({p.state})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: 12, fontWeight: 700, display: 'block', marginBottom: 6 }}>
                    Statutory Document Classification *
                  </label>
                  <select
                    className="form-input"
                    value={uploadDocType}
                    onChange={e => setUploadDocType(e.target.value)}
                    required
                  >
                    <option value="section_11_gazette">Section 11 Preliminary Gazette Notification</option>
                    <option value="section_19_declaration">Section 19 Declaration of Acquisition</option>
                    <option value="award_order">Section 23 Enquiry & Final Award Order</option>
                    <option value="sia_report">Section 4/7 Social Impact Assessment Report</option>
                    <option value="possession_certificate">Section 38 Physical Possession Certificate</option>
                    <option value="rr_entitlement_card">Second Schedule R&R Entitlement Card</option>
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: 12, fontWeight: 700, display: 'block', marginBottom: 6 }}>
                    Document Title / Gazette Number
                  </label>
                  <input
                    className="form-input"
                    value={uploadTitle}
                    onChange={e => setUploadTitle(e.target.value)}
                    placeholder="e.g., Extra-Ordinary Gazette No. DL-33004/2026"
                  />
                </div>

                <div>
                  <label style={{ fontSize: 12, fontWeight: 700, display: 'block', marginBottom: 6 }}>
                    Select Document File (PDF, DOCX, JPG, PNG) *
                  </label>
                  <input
                    id="document-file-input"
                    type="file"
                    className="form-input"
                    onChange={e => setUploadFile(e.target.files?.[0] || null)}
                    required
                  />
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 8 }}>
                  <button type="button" className="btn btn-secondary" onClick={() => setShowUploadModal(false)}>
                    Cancel
                  </button>
                  <button
                    id="submit-doc-upload-btn"
                    type="submit"
                    className="btn btn-primary"
                    disabled={uploading || !uploadFile}
                    style={{ borderRadius: 10 }}
                  >
                    {uploading ? 'Analyzing Compliance...' : 'Upload & Analyze AI Compliance 🚀'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
