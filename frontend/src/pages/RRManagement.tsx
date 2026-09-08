import { useEffect, useState } from 'react';
import { api } from '../api/client';

export default function RRManagement() {
  const [families, setFamilies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState<string | null>(null);

  useEffect(() => {
    load();
  }, []);

  const load = () => {
    setLoading(true);
    api.getRR()
      .then(setFamilies)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  const handleUpdate = async (id: string, newStatus: string) => {
    setUpdating(id);
    try {
      await api.updateRRStatus(id, newStatus, 'Status updated via R&R Manager');
      load();
    } catch (err: any) {
      alert(err.message || 'Failed to update R&R status');
    } finally {
      setUpdating(null);
    }
  };

  if (loading) return <div className="loading-overlay"><div className="spinner" style={{ width: 36, height: 36 }} /></div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)' }}>
            🏡 Rehabilitation & Resettlement (R&R) Management
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>
            LARR Act 2013 Chapter V — Resettlement status tracking for affected displaced families
          </p>
        </div>
        <span className="badge badge-info">{families.length} Affected Families</span>
      </div>

      <div className="card">
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Head of Household</th>
                <th>Family Size</th>
                <th>Annual Income</th>
                <th>Alt Land Provided</th>
                <th>Employment Provided</th>
                <th>R&R Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {families.length === 0 ? (
                <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No family records found.</td></tr>
              ) : (
                families.map(f => (
                  <tr key={f.id}>
                    <td><strong>{f.head_of_household}</strong></td>
                    <td>{f.family_size} Members</td>
                    <td>₹{(f.annual_income || 0).toLocaleString()}</td>
                    <td>{f.alternative_land_provided ? '✓ Yes' : '✗ Pending'}</td>
                    <td>{f.employment_provided ? '✓ Offered' : '✗ Pending'}</td>
                    <td>
                      <span className={`badge ${f.r_and_r_status === 'resettled' ? 'badge-success' : 'badge-warning'}`}>
                        {(f.r_and_r_status || 'pending').replace(/_/g, ' ').toUpperCase()}
                      </span>
                    </td>
                    <td>
                      {f.r_and_r_status !== 'resettled' && (
                        <button className="btn btn-success btn-sm" onClick={() => handleUpdate(f.id, 'resettled')} disabled={updating === f.id}>
                          Mark Resettled ✓
                        </button>
                      )}
                    </td>
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
