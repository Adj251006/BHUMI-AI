import { useEffect, useState } from 'react';
import { api } from '../api/client';

export default function AuditLog() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAuditLogs()
      .then(setLogs)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-overlay"><div className="spinner" style={{ width: 36, height: 36 }} /></div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)' }}>
            🔒 Immutable CAG Audit Trail Log
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>
            Full system transaction logs, status updates, dispute resolutions, and verification review history
          </p>
        </div>
        <span className="badge badge-info">{logs.length} Log Entries</span>
      </div>

      <div className="card">
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>User / Email</th>
                <th>Role</th>
                <th>Action</th>
                <th>Entity Type / ID</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {logs.length === 0 ? (
                <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No audit logs recorded yet.</td></tr>
              ) : (
                logs.map(l => (
                  <tr key={l.id}>
                    <td>{l.timestamp ? new Date(l.timestamp).toLocaleString() : 'N/A'}</td>
                    <td><strong>{l.user_email}</strong></td>
                    <td><span className="badge badge-info">{l.user_role}</span></td>
                    <td><span className="badge badge-success">{l.action}</span></td>
                    <td>{l.entity_type} / {l.entity_id?.slice(0, 8)}...</td>
                    <td style={{ fontSize: 12 }}>{l.description || JSON.stringify(l.new_value)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
