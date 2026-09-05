import { useEffect, useState } from 'react';
import { api } from '../api/client';

export default function Disputes() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [resolving, setResolving] = useState<string | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState<Record<string, string>>({});

  const load = () => {
    api.getDisputes().then(setItems).catch(console.error).finally(() => setLoading(false));
  };
  useEffect(() => { load(); }, []);

  const resolve = async (id: string) => {
    const notes = resolutionNotes[id] || 'Resolved by district authority';
    setResolving(id);
    try { await api.resolveDispute(id, notes); load(); } catch (e) { console.error(e); }
    finally { setResolving(null); }
  };

  if (loading) return <div className="loading-overlay"><div className="spinner" style={{ width: 36, height: 36 }} /></div>;

  const open = items.filter(i => i.status === 'open');
  const underReview = items.filter(i => i.status === 'under_review');
  const resolved = items.filter(i => i.status === 'resolved');

  return (
    <div className="fade-in">
      <div className="section-header mb-4">
        <div>
          <div className="section-title">⚖️ Dispute Management</div>
          <div className="section-subtitle">Land acquisition disputes — {items.length} total</div>
        </div>
      </div>

      <div className="kpi-grid mb-6" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
        <div className="kpi-card red"><div className="kpi-icon red">🔴</div><div className="kpi-value">{open.length}</div><div className="kpi-label">Open Disputes</div></div>
        <div className="kpi-card saffron"><div className="kpi-icon saffron">🔄</div><div className="kpi-value">{underReview.length}</div><div className="kpi-label">Under Review</div></div>
        <div className="kpi-card green"><div className="kpi-icon green">✅</div><div className="kpi-value">{resolved.length}</div><div className="kpi-label">Resolved</div></div>
        <div className="kpi-card teal"><div className="kpi-icon teal">📊</div><div className="kpi-value">{items.length > 0 ? Math.round((resolved.length / items.length) * 100) : 0}%</div><div className="kpi-label">Resolution Rate</div></div>
      </div>

      <div className="alert high mb-4">
        <span>🔴</span>
        <div><strong>7 Critical Disputes</strong> are blocking possession of high-impact parcels on RJ-HWY-024. AI estimates resolving these would reduce project delay risk by 29%.</div>
      </div>

      <div className="card">
        <div className="card-header">
          <div className="card-title">All Disputes</div>
          <button className="btn btn-primary btn-sm">+ File Dispute</button>
        </div>
        <table className="data-table">
          <thead>
            <tr><th>Title</th><th>Type</th><th>Status</th><th>Court Case</th><th>Hearing Date</th><th>Action</th></tr>
          </thead>
          <tbody>
            {items.map((d: any) => (
              <tr key={d.id}>
                <td>
                  <div style={{ fontWeight: 600, fontSize: 13, maxWidth: 280, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{d.title}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2, maxWidth: 280, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{d.description}</div>
                </td>
                <td><span className="badge info">{d.dispute_type}</span></td>
                <td><span className={`badge ${d.status}`}>{d.status}</span></td>
                <td style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{d.court_case_number || '—'}</td>
                <td style={{ fontSize: 12 }}>{d.hearing_date ? new Date(d.hearing_date).toLocaleDateString('en-IN') : '—'}</td>
                <td>
                  {d.status !== 'resolved' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                      <input
                        style={{ fontSize: 11, padding: '4px 8px', border: '1px solid var(--border)', borderRadius: 6, outline: 'none', width: 150 }}
                        placeholder="Resolution notes..."
                        value={resolutionNotes[d.id] || ''}
                        onChange={e => setResolutionNotes(prev => ({ ...prev, [d.id]: e.target.value }))}
                      />
                      <button
                        className="btn btn-primary btn-sm"
                        disabled={resolving === d.id}
                        onClick={() => resolve(d.id)}
                      >
                        {resolving === d.id ? '...' : '✓ Resolve'}
                      </button>
                    </div>
                  )}
                  {d.status === 'resolved' && (
                    <div>
                      <span style={{ color: 'var(--green)', fontWeight: 700, fontSize: 12 }}>✓ Resolved</span>
                      {d.resolved_at && <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{new Date(d.resolved_at).toLocaleDateString('en-IN')}</div>}
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
