import { useEffect, useState } from 'react';
import { api } from '../api/client';

export default function FieldDashboard() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTask, setSelectedTask] = useState<any>(null);
  const [submitting, setSubmitting] = useState(false);
  const [gpsLat, setGpsLat] = useState('26.9124');
  const [gpsLon, setGpsLon] = useState('75.7873');
  const [notes, setNotes] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    load();
  }, []);

  const load = () => {
    setLoading(true);
    api.getTasks()
      .then(setTasks)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTask) return;
    setSubmitting(true);
    setMessage('');

    try {
      const res = await api.submitVerification({
        parcel_id: selectedTask.parcel_id || 'aaaaaaaa-0001-4000-8000-000000000001',
        task_id: selectedTask.id,
        gps_latitude: parseFloat(gpsLat),
        gps_longitude: parseFloat(gpsLon),
        registered_latitude: 26.9200,
        registered_longitude: 75.7900,
        notes: notes,
      });
      setMessage(res.message);
      load();
      setSelectedTask(null);
    } catch (err: any) {
      setMessage(err.message || 'Submission failed');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="loading-overlay"><div className="spinner" style={{ width: 36, height: 36 }} /></div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)' }}>
            📍 Field Officer On-Ground Inspection Portal
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>
            Mobile-first field verification, GPS coordinate validation, and document upload
          </p>
        </div>
        <span className="badge badge-info">{tasks.length} Assigned Tasks</span>
      </div>

      {message && (
        <div style={{ padding: 14, background: 'var(--teal-light)', color: 'var(--teal-dark)', borderRadius: 8, fontWeight: 600 }}>
          ✓ {message}
        </div>
      )}

      {/* TASKS LIST */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">📋 Assigned Inspection Tasks</h3>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Task Title</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Due Date</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {tasks.length === 0 ? (
                <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No assigned tasks.</td></tr>
              ) : (
                tasks.map(t => (
                  <tr key={t.id}>
                    <td><strong>{t.title}</strong></td>
                    <td>
                      <span className={`badge ${t.priority === 'critical' ? 'badge-error' : t.priority === 'high' ? 'badge-warning' : 'badge-info'}`}>
                        {t.priority?.toUpperCase()}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${t.status === 'completed' ? 'badge-success' : 'badge-warning'}`}>
                        {t.status?.toUpperCase()}
                      </span>
                    </td>
                    <td>{t.due_date ? new Date(t.due_date).toLocaleDateString() : 'N/A'}</td>
                    <td>
                      <button className="btn btn-primary btn-sm" onClick={() => setSelectedTask(t)}>
                        Start Verification →
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* VERIFICATION MODAL */}
      {selectedTask && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.5)', zIndex: 1000,
          display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20
        }}>
          <div style={{ background: 'white', borderRadius: 16, width: '100%', maxWidth: 540, padding: 24 }}>
            <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>
              📍 Field Inspection: {selectedTask.title}
            </h3>
            <form onSubmit={handleVerify} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div>
                <label className="form-label">Captured GPS Latitude</label>
                <input className="form-input" value={gpsLat} onChange={e => setGpsLat(e.target.value)} required />
              </div>
              <div>
                <label className="form-label">Captured GPS Longitude</label>
                <input className="form-input" value={gpsLon} onChange={e => setGpsLon(e.target.value)} required />
              </div>
              <div>
                <label className="form-label">Inspection Field Notes</label>
                <textarea className="form-input" rows={3} value={notes} onChange={e => setNotes(e.target.value)} placeholder="Enter observations on land boundary, crops, structures..." required />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
                <button type="button" className="btn btn-outline" onClick={() => setSelectedTask(null)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>Submit Verification</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
