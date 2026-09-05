import { useEffect, useState } from 'react';
import { api } from '../api/client';

export default function Workflow() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState('');

  const load = () => {
    api.getTasks().then(setTasks).catch(console.error).finally(() => setLoading(false));
  };
  useEffect(() => { load(); }, []);

  const updateStatus = async (id: string, status: string) => {
    setUpdating(id);
    try { await api.updateTaskStatus(id, status); load(); } catch (e) { console.error(e); }
    finally { setUpdating(null); }
  };

  const filtered = statusFilter ? tasks.filter(t => t.status === statusFilter) : tasks;
  const overdue = tasks.filter(t => t.due_date && new Date(t.due_date) < new Date() && t.status !== 'completed');

  if (loading) return <div className="loading-overlay"><div className="spinner" style={{ width: 36, height: 36 }} /></div>;

  return (
    <div className="fade-in">
      <div className="section-header mb-4">
        <div>
          <div className="section-title">🔄 Workflow Management</div>
          <div className="section-subtitle">Track tasks across all acquisition lifecycle stages</div>
        </div>
        <button className="btn btn-primary">+ Create Task</button>
      </div>

      {/* Stats */}
      <div className="kpi-grid mb-4" style={{ gridTemplateColumns: 'repeat(5, 1fr)' }}>
        {[
          { label: 'Total Tasks', value: tasks.length, color: 'teal' },
          { label: 'In Progress', value: tasks.filter(t => t.status === 'in_progress').length, color: 'teal' },
          { label: 'Pending Review', value: tasks.filter(t => t.status === 'pending_review').length, color: 'saffron' },
          { label: 'Overdue', value: overdue.length, color: 'red' },
          { label: 'Completed', value: tasks.filter(t => t.status === 'completed').length, color: 'green' },
        ].map(s => (
          <div key={s.label} className={`kpi-card ${s.color}`} style={{ padding: 16 }}>
            <div className="kpi-value" style={{ fontSize: 28 }}>{s.value}</div>
            <div className="kpi-label">{s.label}</div>
          </div>
        ))}
      </div>

      {overdue.length > 0 && (
        <div className="alert critical mb-4">
          <span>🔴</span>
          <div><strong>{overdue.length} overdue task{overdue.length > 1 ? 's' : ''}</strong> require immediate attention. These have been flagged for escalation.</div>
        </div>
      )}

      {/* Filter tabs */}
      <div className="tabs mb-4" style={{ maxWidth: 600 }}>
        {['', 'in_progress', 'pending_review', 'overdue', 'completed'].map(s => (
          <button key={s} className={`tab ${statusFilter === s ? 'active' : ''}`} onClick={() => setStatusFilter(s)}>
            {s === '' ? 'All' : s.replace(/_/g, ' ')}
          </button>
        ))}
      </div>

      <div className="card">
        <table className="data-table">
          <thead>
            <tr><th>Task</th><th>Stage</th><th>Priority</th><th>Status</th><th>Assigned To</th><th>Due Date</th><th>Actions</th></tr>
          </thead>
          <tbody>
            {filtered.map((t: any) => {
              const isOverdue = t.due_date && new Date(t.due_date) < new Date() && t.status !== 'completed';
              return (
                <tr key={t.id} style={{ background: isOverdue ? 'var(--red-bg)' : 'transparent' }}>
                  <td>
                    <div style={{ fontWeight: 600, fontSize: 13, maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.title}</div>
                    {t.is_escalated && <span className="badge high" style={{ marginTop: 4 }}>🔴 Escalated</span>}
                  </td>
                  <td><span className="badge info">{t.stage}</span></td>
                  <td><span className={`badge ${t.priority}`}>{t.priority}</span></td>
                  <td><span className={`badge ${t.status}`}>{t.status.replace(/_/g, ' ')}</span></td>
                  <td style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{t.assigned_to ? '👤 Officer' : '—'}</td>
                  <td style={{ fontSize: 12, color: isOverdue ? 'var(--red)' : 'var(--text-secondary)', fontWeight: isOverdue ? 700 : 400 }}>
                    {t.due_date ? new Date(t.due_date).toLocaleDateString('en-IN') : '—'}
                    {isOverdue && <div style={{ fontSize: 10 }}>⚠️ OVERDUE</div>}
                  </td>
                  <td>
                    {t.status === 'in_progress' && (
                      <button className="btn btn-secondary btn-sm" disabled={updating === t.id} onClick={() => updateStatus(t.id, 'pending_review')}>
                        {updating === t.id ? '...' : 'Submit'}
                      </button>
                    )}
                    {t.status === 'pending_review' && (
                      <div style={{ display: 'flex', gap: 4 }}>
                        <button className="btn btn-primary btn-sm" disabled={updating === t.id} onClick={() => updateStatus(t.id, 'approved')}>Approve</button>
                        <button className="btn btn-ghost btn-sm" onClick={() => updateStatus(t.id, 'rejected')}>Reject</button>
                      </div>
                    )}
                    {t.status === 'approved' && <span style={{ color: 'var(--green)', fontWeight: 600, fontSize: 12 }}>✓ Approved</span>}
                    {isOverdue && t.status !== 'completed' && (
                      <button className="btn btn-danger btn-sm" onClick={() => updateStatus(t.id, 'escalated')}>Escalate</button>
                    )}
                  </td>
                </tr>
              );
            })}
            {filtered.length === 0 && <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 32 }}>No tasks found</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
