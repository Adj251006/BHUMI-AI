import { useEffect, useState } from 'react';
import { api } from '../api/client';

export default function Documents() {
  const [docs, setDocs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [aiResult, setAiResult] = useState<any>(null);

  useEffect(() => {
    api.getDocuments().then(setDocs).catch(console.error).finally(() => setLoading(false));
  }, []);

  const analyzeDemo = async () => {
    setAnalyzing(true);
    try { const r = await api.analyzeDocument(); setAiResult(r); } catch (e) { console.error(e); }
    finally { setAnalyzing(false); }
  };

  if (loading) return <div className="loading-overlay"><div className="spinner" style={{ width: 36, height: 36 }} /></div>;

  return (
    <div className="fade-in">
      <div className="section-header mb-4">
        <div>
          <div className="section-title">📄 Document Management</div>
          <div className="section-subtitle">AI-powered document intelligence and validation</div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-secondary" onClick={analyzeDemo} disabled={analyzing}>
            {analyzing ? <><span className="spinner" />Analyzing...</> : '🤖 AI Analyze Demo'}
          </button>
          <button className="btn btn-primary">+ Upload Document</button>
        </div>
      </div>

      {/* AI Analysis Result */}
      {aiResult && (
        <div className="card mb-6">
          <div className="card-header">
            <div className="card-title">🤖 AI Document Intelligence Result</div>
            <span className={`badge ${aiResult.validation_result.status === 'approved' ? 'approved' : 'pending'}`}>
              {Math.round(aiResult.overall_confidence * 100)}% confidence
            </span>
          </div>
          <div style={{ padding: 24 }}>
            <div className="alert high mb-4">
              <span>⚠️</span>
              <div>
                <strong>Requires Review:</strong> {aiResult.validation_result.issues.join(' · ')}
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 12 }}>
              {Object.entries(aiResult.extracted_fields).map(([key, val]: [string, any]) => (
                <div key={key} style={{
                  padding: 14, borderRadius: 10, border: `1.5px solid ${val.status === 'matched' ? 'var(--green)' : val.status === 'mismatch' ? 'var(--saffron)' : 'var(--red)'}`,
                  background: val.status === 'matched' ? 'var(--green-bg)' : val.status === 'mismatch' ? 'var(--saffron-bg)' : 'var(--red-bg)',
                }}>
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
                  {val.note && <div style={{ fontSize: 10, color: 'var(--text-secondary)', marginTop: 4, fontStyle: 'italic' }}>{val.note}</div>}
                </div>
              ))}
            </div>
            <div style={{ marginTop: 16, fontSize: 11, color: 'var(--text-muted)', fontStyle: 'italic' }}>{aiResult.disclaimer}</div>
          </div>
        </div>
      )}

      {/* Document List */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">All Documents</div>
          <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>{docs.length} documents</span>
        </div>
        <table className="data-table">
          <thead>
            <tr><th>Document</th><th>Type</th><th>Version</th><th>Status</th><th>AI Validation</th><th>Actions</th></tr>
          </thead>
          <tbody>
            {docs.map((d: any) => (
              <tr key={d.id}>
                <td>
                  <div style={{ fontWeight: 600, fontSize: 13 }}>{d.title}</div>
                  {d.file_name && <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>📎 {d.file_name}</div>}
                </td>
                <td><span className="badge info" style={{ textTransform: 'none', fontSize: 10 }}>{d.document_type.replace(/_/g, ' ')}</span></td>
                <td><span style={{ fontSize: 12, fontWeight: 600 }}>v{d.version}</span></td>
                <td><span className={`badge ${d.status}`}>{d.status.replace(/_/g, ' ')}</span></td>
                <td>
                  {d.ai_confidence_score ? (
                    <div>
                      <div style={{ fontWeight: 700, fontSize: 13, color: d.ai_confidence_score > 0.8 ? 'var(--green)' : 'var(--saffron)' }}>
                        {Math.round(d.ai_confidence_score * 100)}%
                      </div>
                      {d.validation_result?.issues?.length > 0 && (
                        <div style={{ fontSize: 10, color: 'var(--red)', marginTop: 2 }}>
                          ⚠️ {d.validation_result.issues.length} issue(s)
                        </div>
                      )}
                    </div>
                  ) : <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>Not analyzed</span>}
                </td>
                <td>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <button className="btn btn-ghost btn-sm">View</button>
                    {d.status === 'under_review' && <button className="btn btn-primary btn-sm">Approve</button>}
                  </div>
                </td>
              </tr>
            ))}
            {docs.length === 0 && <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 32 }}>No documents. Upload to get started.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
