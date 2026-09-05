import { useEffect, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
  PieChart, Pie, Line, Area, AreaChart,
} from 'recharts';
import { api } from '../api/client';
import { useNavigate } from 'react-router-dom';

export default function Analytics() {
  const navigate = useNavigate();
  const [analytics, setAnalytics] = useState<any>(null);
  const [anomalies, setAnomalies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.getNationalAnalytics(), api.getAnomalies()])
      .then(([a, an]) => { setAnalytics(a); setAnomalies(an); })
      .catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-overlay"><div className="spinner" style={{ width: 36, height: 36 }} /></div>;

  const a = analytics || {};
  const stateData = (a.state_breakdown || []).slice(0, 10);

  const riskDistribution = [
    { level: 'Critical', count: 1, color: '#C0392B' },
    { level: 'High', count: 3, color: '#E74C3C' },
    { level: 'Medium', count: 8, color: '#F39C12' },
    { level: 'Low', count: 10, color: '#27AE60' },
  ];

  const monthlyData = [
    { month: 'Apr', parcels: 1200, compensation: 120, disputes_resolved: 8 },
    { month: 'May', parcels: 1560, compensation: 175, disputes_resolved: 12 },
    { month: 'Jun', parcels: 1920, compensation: 245, disputes_resolved: 18 },
    { month: 'Jul', parcels: 2340, compensation: 320, disputes_resolved: 22 },
    { month: 'Aug', parcels: 2890, compensation: 410, disputes_resolved: 31 },
    { month: 'Sep', parcels: 3100, compensation: 450, disputes_resolved: 35 },
  ];

  return (
    <div className="fade-in">
      <div className="section-header mb-6">
        <div>
          <div className="section-title">📊 National Analytics</div>
          <div className="section-subtitle">Consolidated view across all states and projects</div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-secondary btn-sm" onClick={() => navigate('/simulator')}>🔬 Simulator</button>
          <button className="btn btn-primary btn-sm">📥 Export Report</button>
        </div>
      </div>

      {/* KPIs */}
      <div className="kpi-grid mb-6">
        <div className="kpi-card teal"><div className="kpi-icon teal">📋</div><div className="kpi-value">{a.total_projects ?? 0}</div><div className="kpi-label">Total Projects</div><div className="kpi-trend neutral">🗾 {stateData.length} active states</div></div>
        <div className="kpi-card green"><div className="kpi-icon green">🗺️</div><div className="kpi-value">{(a.acquisition_percentage ?? 0).toFixed(0)}%</div><div className="kpi-label">Acquisition Rate</div><div className="kpi-trend up">{a.acquired_parcels ?? 0} of {a.total_parcels ?? 0} parcels</div></div>
        <div className="kpi-card saffron"><div className="kpi-icon saffron">💰</div><div className="kpi-value">₹{(a.compensation_paid_crore ?? 0).toFixed(1)}Cr</div><div className="kpi-label">Disbursed</div><div className="kpi-trend down">{a.compensation_pending_count ?? 0} pending cases</div></div>
        <div className="kpi-card red"><div className="kpi-icon red">🚨</div><div className="kpi-value">{a.high_risk_projects ?? 0}</div><div className="kpi-label">High Risk Projects</div><div className="kpi-trend down">{a.disputed_parcels ?? 0} open disputes</div></div>
      </div>

      {/* ROW 1 */}
      <div className="grid-2 mb-6">
        {/* State breakdown */}
        <div className="card">
          <div className="card-header"><div className="card-title">🗾 Acquisition by State</div></div>
          <div style={{ padding: '8px 16px 16px' }}>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={stateData} layout="vertical" margin={{ left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="state" tick={{ fontSize: 11 }} width={100} />
                <Tooltip contentStyle={{ borderRadius: 8, fontSize: 12 }} />
                <Bar dataKey="active" fill="#1B6CA8" name="Active" radius={[0, 3, 3, 0]} />
                <Bar dataKey="completed" fill="#27AE60" name="Completed" radius={[0, 3, 3, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Risk distribution */}
        <div className="card">
          <div className="card-header"><div className="card-title">🚨 Risk Level Distribution</div></div>
          <div style={{ padding: '8px 20px 20px' }}>
            <ResponsiveContainer width="100%" height={160}>
              <PieChart>
                <Pie data={riskDistribution} cx="50%" cy="50%" innerRadius={40} outerRadius={75} paddingAngle={3} dataKey="count">
                  {riskDistribution.map((d, i) => <Cell key={i} fill={d.color} />)}
                </Pie>
                <Tooltip contentStyle={{ borderRadius: 8, fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ display: 'flex', justifyContent: 'center', gap: 20, flexWrap: 'wrap', marginTop: 8 }}>
              {riskDistribution.map(r => (
                <div key={r.level} style={{ textAlign: 'center' }}>
                  <div style={{ fontWeight: 800, fontSize: 20, color: r.color }}>{r.count}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 4 }}>
                    <span style={{ width: 8, height: 8, borderRadius: '50%', background: r.color, display: 'inline-block' }} />
                    {r.level}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ROW 2 */}
      <div className="grid-2 mb-6">
        {/* Monthly trend */}
        <div className="card" style={{ gridColumn: 'span 2' }}>
          <div className="card-header"><div className="card-title">📈 Monthly Progress Trends</div></div>
          <div style={{ padding: '8px 20px 20px' }}>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={monthlyData}>
                <defs>
                  <linearGradient id="parcGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#1B6CA8" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#1B6CA8" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="compGrad2" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#27AE60" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#27AE60" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ borderRadius: 8, fontSize: 12 }} />
                <Area type="monotone" dataKey="parcels" stroke="#1B6CA8" fill="url(#parcGrad)" strokeWidth={2} name="Parcels Processed" />
                <Area type="monotone" dataKey="compensation" stroke="#27AE60" fill="url(#compGrad2)" strokeWidth={2} name="Comp Disbursed (₹Cr)" />
                <Line type="monotone" dataKey="disputes_resolved" stroke="#E67E22" strokeWidth={2} dot={{ r: 4, fill: '#E67E22' }} name="Disputes Resolved" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Anomalies */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">🤖 AI Anomaly Detection Log</div>
          <span className="badge high">{anomalies.length} anomalies</span>
        </div>
        <table className="data-table">
          <thead>
            <tr><th>Entity</th><th>Anomaly Type</th><th>Severity</th><th>Description</th><th>Detected Value</th><th>Status</th></tr>
          </thead>
          <tbody>
            {anomalies.map((a: any) => (
              <tr key={a.id}>
                <td><div style={{ fontWeight: 600, fontSize: 12 }}>{a.entity_type}</div><div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{a.entity_id?.slice(0, 12)}...</div></td>
                <td><span className="badge info" style={{ fontSize: 10 }}>{a.anomaly_type.replace(/_/g, ' ')}</span></td>
                <td><span className={`badge ${a.severity}`}>{a.severity}</span></td>
                <td style={{ fontSize: 12, maxWidth: 280 }}>{a.description}</td>
                <td style={{ fontSize: 12, fontFamily: 'monospace', color: 'var(--saffron)' }}>{a.detected_value || '—'}</td>
                <td><span className={`badge ${a.is_resolved ? 'resolved' : 'open'}`}>{a.is_resolved ? 'Resolved' : 'Open'}</span></td>
              </tr>
            ))}
            {anomalies.length === 0 && <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 32 }}>No anomalies detected</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
