import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const DEFAULT_DISTRICT_BREAKDOWN = [
  { district: 'Jaipur', projects: 3, active: 2 },
  { district: 'Jodhpur', projects: 2, active: 2 },
  { district: 'Udaipur', projects: 2, active: 1 },
  { district: 'Ajmer', projects: 1, active: 1 },
];

const DEFAULT_STATE_PROJECTS = [
  { id: '12345678-1234-5678-1234-567812345678', name: 'Delhi-Jaipur Highway Expansion (NH-48)', district: 'Jaipur', status: 'active' },
  { id: 'proj-rj-002', name: 'Jaipur Outer Ring Road Phase II', district: 'Jaipur', status: 'active' },
  { id: 'proj-rj-003', name: 'Jodhpur Solar Park Feeder Line', district: 'Jodhpur', status: 'active' },
  { id: 'proj-rj-004', name: 'Udaipur Smart Logistics Hub', district: 'Udaipur', status: 'active' },
  { id: 'proj-rj-005', name: 'Ajmer-Pushkar Rail Link', district: 'Ajmer', status: 'active' },
  { id: 'proj-rj-006', name: 'Kota Industrial Corridor Access Road', district: 'Kota', status: 'completed' },
];

export default function StateDashboard() {
  const { stateName } = useParams<{ stateName: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const state = stateName || 'Rajasthan';

  useEffect(() => {
    setLoading(true);
    api.getStateAnalytics(state)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [state]);

  if (loading) return <div className="loading-overlay"><div className="spinner" style={{ width: 36, height: 36 }} /></div>;

  const d = data || {};
  const districtBreakdown = (d.district_breakdown && d.district_breakdown.length > 0)
    ? d.district_breakdown
    : DEFAULT_DISTRICT_BREAKDOWN;

  const projectsList = (d.projects && d.projects.length > 0)
    ? d.projects
    : DEFAULT_STATE_PROJECTS;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* HEADER */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <button className="btn btn-ghost btn-sm" onClick={() => navigate('/dashboard')} style={{ marginBottom: 8 }}>
            ← Back to National Command Center
          </button>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)' }}>
            🏛️ {state} State Land Acquisition Command
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>
            State-level monitoring, district performance breakdown, and project tracking
          </p>
        </div>
        <span className="badge badge-info" style={{ fontSize: 13, padding: '6px 14px' }}>
          {d.total_projects || projectsList.length} Total Projects
        </span>
      </div>

      {/* KPIS */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-header"><span className="kpi-title">Active Projects</span><span>📋</span></div>
          <div className="kpi-value">{d.active_projects || projectsList.filter((p: any) => p.status === 'active').length}</div>
          <div className="kpi-footer text-muted">Projects currently in acquisition phase</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-header"><span className="kpi-title">Total Parcels</span><span>🗺️</span></div>
          <div className="kpi-value">{d.total_parcels || 5400}</div>
          <div className="kpi-footer text-success">{d.acquired_parcels || 4428} possessed ({d.acquisition_percentage || 82}%)</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-header"><span className="kpi-title">District Authorities</span><span>🏙️</span></div>
          <div className="kpi-value">{districtBreakdown.length}</div>
          <div className="kpi-footer text-muted">Districts executing acquisition</div>
        </div>
      </div>

      {/* DISTRICT BREAKDOWN CHART */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">🏙️ District-wise Projects Distribution ({state})</h3>
        </div>
        <div style={{ height: 260 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={districtBreakdown}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="district" stroke="var(--text-muted)" fontSize={12} />
              <YAxis stroke="var(--text-muted)" fontSize={12} />
              <Tooltip />
              <Bar dataKey="projects" fill="#1B6CA8" radius={[4, 4, 0, 0]} name="Total Projects" />
              <Bar dataKey="active" fill="#27AE60" radius={[4, 4, 0, 0]} name="Active Projects" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* PROJECTS LIST IN STATE */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">📋 State Projects List ({state})</h3>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Project Name</th>
                <th>District</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {projectsList.map((p: any) => (
                <tr key={p.id}>
                  <td><strong>{p.name}</strong></td>
                  <td>{p.district || 'State-wide'}</td>
                  <td>
                    <span className={`badge ${p.status === 'active' || p.status === 'In Progress' ? 'badge-success' : 'badge-warning'}`}>
                      {(p.status || 'ACTIVE').toUpperCase()}
                    </span>
                  </td>
                  <td>
                    <button className="btn btn-outline btn-sm" onClick={() => navigate(`/project/${p.id}`)}>
                      Open Project →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
