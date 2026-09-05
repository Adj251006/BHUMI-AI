import { useEffect, useState } from 'react';
import { api } from '../api/client';

export default function Compensation() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [updating, setUpdating] = useState<string | null>(null);

  const load = () => {
    api.getCompensation(filter || undefined).then(setItems).catch(console.error).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [filter]);

  const updateStatus = async (id: string, status: string) => {
    setUpdating(id);
    try { await api.updateCompensationStatus(id, status); load(); } catch (e) { console.error(e); }
    finally { setUpdating(null); }
  };

  const stats = {
    total: items.length,
    pending: items.filter(i => i.status === 'pending').length,
    processing: items.filter(i => i.status === 'under_verification' || i.status === 'processing').length,
    disbursed: items.filter(i => i.status === 'disbursed').length,
    totalAmount: items.reduce((s, i) => s + i.disbursed_amount, 0),
  };

  if (loading) return <div className="loading-overlay"><div className="spinner" style={{ width: 36, height: 36 }} /></div>;

  return (
    <div className="fade-in">
      <div className="section-header mb-4">
        <div>
          <div className="section-title">💰 Compensation Management</div>
          <div className="section-subtitle">Monitor and process compensation disbursements</div>
        </div>
      </div>

      {/* Stats */}
      <div className="kpi-grid mb-6" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
        <div className="kpi-card saffron"><div className="kpi-icon saffron">⏳</div><div className="kpi-value">{stats.pending}</div><div className="kpi-label">Pending</div></div>
        <div className="kpi-card teal"><div className="kpi-icon teal">🔄</div><div className="kpi-value">{stats.processing}</div><div className="kpi-label">Under Verification</div></div>
        <div className="kpi-card green"><div className="kpi-icon green">✅</div><div className="kpi-value">{stats.disbursed}</div><div className="kpi-label">Disbursed</div></div>
        <div className="kpi-card purple"><div className="kpi-icon purple">💎</div><div className="kpi-value">₹{(stats.totalAmount / 1e7).toFixed(0)}Cr</div><div className="kpi-label">Total Amount</div></div>
      </div>

      {/* Anomaly Alert */}
      <div className="alert high mb-4">
        <span>⚠️</span>
        <div>
          <strong>AI Anomaly Detected:</strong> One compensation case has an unusually high value of ₹1.8Cr — 4.2x the district average for similar land type.
          Recommend manual review before processing.
        </div>
        <button className="btn btn-secondary btn-sm">Review</button>
      </div>

      {/* Filter */}
      <div className="filter-bar mb-4">
        <div className="tabs" style={{ maxWidth: 500 }}>
          {['', 'pending', 'under_verification', 'disbursed'].map(s => (
            <button key={s} className={`tab ${filter === s ? 'active' : ''}`} onClick={() => setFilter(s)}>
              {s === '' ? 'All' : s === 'pending' ? `Pending (${stats.pending})` : s === 'under_verification' ? 'Verification' : `Disbursed (${stats.disbursed})`}
            </button>
          ))}
        </div>
      </div>

      <div className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Beneficiary</th>
              <th>Account</th>
              <th>Amount</th>
              <th>Status</th>
              <th>Disbursed</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.slice(0, 20).map((c: any) => (
              <tr key={c.id}>
                <td style={{ fontWeight: 600 }}>{c.beneficiary_name}</td>
                <td style={{ fontSize: 12, fontFamily: 'monospace' }}>{c.beneficiary_account || '—'}</td>
                <td style={{ fontWeight: 700 }}>
                  ₹{(c.disbursed_amount / 1e5).toFixed(1)}L
                  {c.disbursed_amount > 10000000 && (
                    <span className="badge high" style={{ marginLeft: 6 }}>⚠️ High</span>
                  )}
                </td>
                <td><span className={`badge ${c.status}`}>{c.status}</span></td>
                <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                  {c.disbursed_at ? new Date(c.disbursed_at).toLocaleDateString('en-IN') : '—'}
                  {c.payment_reference && <div style={{ fontSize: 10 }}>{c.payment_reference}</div>}
                </td>
                <td>
                  {c.status === 'pending' && (
                    <div style={{ display: 'flex', gap: 6 }}>
                      <button
                        className="btn btn-secondary btn-sm"
                        disabled={updating === c.id}
                        onClick={() => updateStatus(c.id, 'under_verification')}
                      >
                        Verify
                      </button>
                    </div>
                  )}
                  {c.status === 'under_verification' && (
                    <button
                      className="btn btn-primary btn-sm"
                      disabled={updating === c.id}
                      onClick={() => updateStatus(c.id, 'disbursed')}
                    >
                      {updating === c.id ? '...' : 'Disburse ✓'}
                    </button>
                  )}
                  {c.status === 'disbursed' && <span style={{ color: 'var(--green)', fontSize: 13, fontWeight: 600 }}>✓ Paid</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length > 20 && (
          <div style={{ padding: 16, textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
            Showing 20 of {items.length} records
          </div>
        )}
      </div>
    </div>
  );
}
