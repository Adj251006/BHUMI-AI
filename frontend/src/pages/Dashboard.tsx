import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Line, Area, AreaChart,
} from 'recharts';
import { api } from '../api/client';

interface Analytics {
  total_projects: number;
  active_projects: number;
  completed_projects: number;
  total_parcels: number;
  acquired_parcels: number;
  acquisition_percentage: number;
  land_proposed_hectares: number;
  land_acquired_hectares: number;
  compensation_assessed_crore: number;
  compensation_paid_crore: number;
  compensation_pending_count: number;
  affected_families: number;
  disputed_parcels: number;
  high_risk_projects: number;
  state_breakdown: Array<{ state: string; projects: number; active: number; completed: number }>;
}

const MOCK_TIMELINE = [
  { month: 'Apr', acquired: 24, compensation: 18, rr: 8 },
  { month: 'May', acquired: 32, compensation: 25, rr: 12 },
  { month: 'Jun', acquired: 45, compensation: 38, rr: 18 },
  { month: 'Jul', acquired: 58, compensation: 46, rr: 24 },
  { month: 'Aug', acquired: 74, compensation: 61, rr: 32 },
  { month: 'Sep', acquired: 82, compensation: 72, rr: 38 },
];

const COLORS = ['#1B6CA8', '#27AE60', '#E67E22', '#E74C3C', '#8E44AD', '#16A085'];

export default function Dashboard() {
  const navigate = useNavigate();
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [criticalRisk] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getNationalAnalytics()
      .then((a) => {
        if (a) setAnalytics(a);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="loading-overlay">
      <div className="spinner" style={{ width: 40, height: 40, borderWidth: 3 }} />
      <span>Loading Command Center...</span>
    </div>
  );

  const a = analytics;

  const pieData = [
    { name: 'Acquired', value: a?.acquired_parcels || 410 },
    { name: 'Pending', value: (a?.total_parcels || 500) - (a?.acquired_parcels || 410) },
  ];

  const sectorData = [
    { sector: 'Infrastructure', projects: 8 },
    { sector: 'Water', projects: 4 },
    { sector: 'Housing', projects: 3 },
    { sector: 'Energy', projects: 3 },
    { sector: 'Industrial', projects: 3 },
    { sector: 'Others', projects: 1 },
  ];

  const riskProbPct = criticalRisk ? Math.round(criticalRisk.delay_probability * 100) : 93;
  const delayDays = criticalRisk ? criticalRisk.expected_delay_days : 49;

  return (
    <div className="fade-in">
      {/* Critical Alert Banner */}
      <div className="alert critical mb-4" style={{ cursor: 'pointer' }} onClick={() => navigate('/project/12345678-1234-5678-1234-567812345678')}>
        <span style={{ fontSize: 20 }}>🔴</span>
        <div style={{ flex: 1 }}>
          <strong>CRITICAL ALERT: Delhi-Jaipur Highway (RJ-HWY-024)</strong> has a <strong>{riskProbPct}% delay probability</strong> — expected {delayDays}-day overrun.
          {' '}7 critical disputed parcels require immediate attention.
        </div>
        <button className="btn btn-danger btn-sm">Take Action →</button>
      </div>

      {/* KPI GRID */}
      <div className="kpi-grid mb-6">
        <div className="kpi-card teal" style={{ cursor: 'pointer' }} onClick={() => navigate('/projects')}>
          <div className="kpi-icon teal">📋</div>
          <div className="kpi-value">{a?.total_projects ?? 22}</div>
          <div className="kpi-label">Total Projects</div>
          <div className="kpi-trend neutral">🟢 {a?.active_projects ?? 14} Active</div>
        </div>
        <div className="kpi-card saffron" style={{ cursor: 'pointer' }} onClick={() => navigate('/projects')}>
          <div className="kpi-icon saffron">🗺️</div>
          <div className="kpi-value">{(a?.total_parcels ?? 15241).toLocaleString()}</div>
          <div className="kpi-label">Total Parcels</div>
          <div className="kpi-trend neutral">📍 {a?.acquisition_percentage ?? 82}% acquired</div>
        </div>
        <div className="kpi-card green" style={{ cursor: 'pointer' }} onClick={() => navigate('/compensation')}>
          <div className="kpi-icon green">💰</div>
          <div className="kpi-value">₹{a?.compensation_paid_crore?.toFixed(0) ?? '1,840'}Cr</div>
          <div className="kpi-label">Compensation Disbursed</div>
          <div className="kpi-trend down">⚠️ {a?.compensation_pending_count ?? 52} pending</div>
        </div>
        <div className="kpi-card red" style={{ cursor: 'pointer' }} onClick={() => navigate('/disputes')}>
          <div className="kpi-icon red">⚖️</div>
          <div className="kpi-value">{a?.disputed_parcels ?? 18}</div>
          <div className="kpi-label">Active Disputes</div>
          <div className="kpi-trend down">🔴 7 critical parcels</div>
        </div>
        <div className="kpi-card purple">
          <div className="kpi-icon purple">👨‍👩‍👧‍👦</div>
          <div className="kpi-value">{a?.affected_families ?? 31}</div>
          <div className="kpi-label">R&R Pending Families</div>
          <div className="kpi-trend down">📋 Survey in progress</div>
        </div>
      </div>

      {/* CHARTS ROW */}
      <div className="grid-3 mb-6">
        {/* Progress Timeline */}
        <div className="card" style={{ gridColumn: 'span 2' }}>
          <div className="card-header">
            <div className="card-title">📈 National Progress Timeline</div>
            <span className="badge active">Live</span>
          </div>
          <div style={{ padding: '16px 20px 20px' }}>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={MOCK_TIMELINE}>
                <defs>
                  <linearGradient id="acqGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#1B6CA8" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#1B6CA8" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="compGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#27AE60" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#27AE60" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="month" tick={{ fontSize: 12, fill: 'var(--text-muted)' }} />
                <YAxis tick={{ fontSize: 12, fill: 'var(--text-muted)' }} />
                <Tooltip contentStyle={{ borderRadius: 8, border: '1px solid var(--border)', fontSize: 12 }} />
                <Area type="monotone" dataKey="acquired" stroke="#1B6CA8" strokeWidth={2} fill="url(#acqGrad)" name="Parcels Acquired %" />
                <Area type="monotone" dataKey="compensation" stroke="#27AE60" strokeWidth={2} fill="url(#compGrad)" name="Compensation %" />
                <Line type="monotone" dataKey="rr" stroke="#E67E22" strokeWidth={2} dot={false} name="R&R Progress %" />
              </AreaChart>
            </ResponsiveContainer>
            <div style={{ display: 'flex', gap: 20, marginTop: 12 }}>
              {[['#1B6CA8', 'Parcels Acquired'], ['#27AE60', 'Compensation'], ['#E67E22', 'R&R Progress']].map(([c, l]) => (
                <div key={l as string} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <div style={{ width: 10, height: 10, borderRadius: '50%', background: c as string }} />
                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{l as string}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Parcel Status Pie */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">🗺️ Acquisition Status</div>
          </div>
          <div style={{ padding: '16px 20px' }}>
            <ResponsiveContainer width="100%" height={160}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={45} outerRadius={75} paddingAngle={3} dataKey="value">
                  {pieData.map((_, i) => <Cell key={i} fill={i === 0 ? '#27AE60' : '#E2E8F0'} />)}
                </Pie>
                <Tooltip contentStyle={{ borderRadius: 8, fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ display: 'flex', justifyContent: 'center', gap: 20, marginTop: 8 }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontWeight: 800, fontSize: 22, color: '#27AE60' }}>{a?.acquired_parcels ?? 410}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Acquired</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontWeight: 800, fontSize: 22, color: '#E2E8F0', WebkitTextStroke: '1px #999' }}>{(a?.total_parcels ?? 500) - (a?.acquired_parcels ?? 410)}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Pending</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* SECOND ROW */}
      <div className="grid-2 mb-6">
        {/* State Breakdown */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">🗾 Projects by State</div>
            <button className="btn btn-ghost btn-sm" onClick={() => navigate('/analytics')}>Full Report</button>
          </div>
          <div style={{ padding: '8px 20px 16px' }}>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={(a?.state_breakdown || []).slice(0, 8)} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="state" tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} width={90} />
                <Tooltip contentStyle={{ borderRadius: 8, fontSize: 12 }} />
                <Bar dataKey="active" fill="#1B6CA8" radius={[0, 3, 3, 0]} name="Active" />
                <Bar dataKey="completed" fill="#27AE60" radius={[0, 3, 3, 0]} name="Completed" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Projects at Risk */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">🚨 Projects Requiring Action</div>
            <span className="badge high">4 High Risk</span>
          </div>
          <div style={{ padding: '0' }}>
            {[
              { name: 'Delhi-Jaipur Highway', state: 'Rajasthan', risk: 82, level: 'critical', action: 'View →' },
              { name: 'Gujarat Bullet Train', state: 'Gujarat', risk: 91, level: 'critical', action: 'View →' },
              { name: 'Mumbai-Pune Expressway', state: 'Maharashtra', risk: 45, level: 'medium', action: 'View →' },
              { name: 'UP Expressway Extension', state: 'Uttar Pradesh', risk: 38, level: 'medium', action: 'View →' },
              { name: 'Karnataka Industrial Corridor', state: 'Karnataka', risk: 22, level: 'low', action: 'View →' },
            ].map((p, i) => (
              <div
                key={i}
                style={{ padding: '14px 20px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer', transition: 'background 0.15s' }}
                onClick={() => navigate('/projects')}
                onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, fontSize: 13 }}>{p.name}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>📍 {p.state}</div>
                </div>
                <div style={{ textAlign: 'center', minWidth: 60 }}>
                  <div style={{ fontWeight: 800, fontSize: 18, color: p.risk > 60 ? 'var(--red)' : p.risk > 30 ? 'var(--saffron)' : 'var(--green)' }}>
                    {p.risk}%
                  </div>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>delay risk</div>
                </div>
                <span className={`badge ${p.level}`}>{p.level}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* SECTOR CHART + RECENT ALERTS */}
      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div className="card-title">🏗️ Projects by Sector</div>
          </div>
          <div style={{ padding: '8px 20px 20px' }}>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={sectorData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="sector" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ borderRadius: 8, fontSize: 12 }} />
                <Bar dataKey="projects" radius={[4, 4, 0, 0]}>
                  {sectorData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div className="card-title">🤖 AI Anomaly Feed</div>
            <button className="btn btn-ghost btn-sm" onClick={() => navigate('/analytics')}>See All</button>
          </div>
          <div>
            {[
              { icon: '🔴', title: 'Unusual compensation value: ₹1.8Cr', sub: 'Compensation · 4.2x district average', sev: 'high', time: '1h ago' },
              { icon: '🟠', title: 'GPS mismatch on field verification', sub: 'Field Op · 320m from registered location', sev: 'medium', time: '3h ago' },
              { icon: '🟡', title: 'Duplicate survey number detected', sub: 'Land Parcel 101/1 · Data entry error', sev: 'medium', time: '5h ago' },
              { icon: '🔵', title: '5 approval tasks overdue by >7 days', sub: 'Workflow · District Jaipur', sev: 'info', time: '6h ago' },
            ].map((a, i) => (
              <div key={i} style={{ padding: '12px 20px', borderBottom: '1px solid var(--border)', display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                <span style={{ fontSize: 18, flexShrink: 0 }}>{a.icon}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{a.title}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{a.sub} · {a.time}</div>
                </div>
                <span className={`badge ${a.sev}`}>{a.sev}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
