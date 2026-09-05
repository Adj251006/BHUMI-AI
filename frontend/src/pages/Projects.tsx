import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';

export default function Projects() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState('');
  const [stateFilter, setStateFilter] = useState('');

  useEffect(() => {
    api.getProjects().then(setProjects).catch(console.error).finally(() => setLoading(false));
  }, []);

  const filtered = projects.filter(p => {
    const matchSearch = !search || p.name.toLowerCase().includes(search.toLowerCase()) || p.state?.toLowerCase().includes(search.toLowerCase());
    const matchRisk = !riskFilter || p.risk_level === riskFilter;
    const matchState = !stateFilter || p.state === stateFilter;
    return matchSearch && matchRisk && matchState;
  });

  const states = [...new Set(projects.map(p => p.state).filter(Boolean))].sort();

  if (loading) return <div className="loading-overlay"><div className="spinner" style={{ width: 40, height: 40 }} /><span>Loading projects...</span></div>;

  return (
    <div className="fade-in">
      <div className="section-header mb-4">
        <div>
          <div className="section-title">All Projects</div>
          <div className="section-subtitle">{projects.length} projects across India</div>
        </div>
        <button className="btn btn-primary">+ New Project</button>
      </div>

      {/* Filters */}
      <div className="filter-bar mb-4">
        <div className="search-input">
          <span className="search-icon">🔍</span>
          <input placeholder="Search projects, states..." value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <select className="form-control" style={{ width: 160 }} value={riskFilter} onChange={e => setRiskFilter(e.target.value)}>
          <option value="">All Risk Levels</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <select className="form-control" style={{ width: 160 }} value={stateFilter} onChange={e => setStateFilter(e.target.value)}>
          <option value="">All States</option>
          {states.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>{filtered.length} results</span>
      </div>

      {/* Project Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: 16 }}>
        {filtered.map(p => (
          <div
            key={p.id}
            className="card card-hover"
            onClick={() => navigate(`/project/${p.id}`)}
            style={{ borderLeft: `4px solid ${p.risk_level === 'critical' ? 'var(--red)' : p.risk_level === 'high' ? 'var(--saffron)' : p.risk_level === 'medium' ? 'var(--yellow)' : 'var(--green)'}` }}
          >
            <div style={{ padding: '20px 20px 16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                <div style={{ flex: 1, paddingRight: 12 }}>
                  <div style={{ fontWeight: 700, fontSize: 14, lineHeight: 1.3, marginBottom: 4 }}>{p.name}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>📍 {p.state}{p.district ? ` · ${p.district}` : ''} · {p.ministry}</div>
                </div>
                <div style={{ textAlign: 'center', flexShrink: 0 }}>
                  <div style={{ fontSize: 22, fontWeight: 800, color: (p.delay_probability || 0) > 0.6 ? 'var(--red)' : (p.delay_probability || 0) > 0.3 ? 'var(--saffron)' : 'var(--green)' }}>
                    {Math.round((p.delay_probability || 0) * 100)}%
                  </div>
                  <div style={{ fontSize: 9, color: 'var(--text-muted)', letterSpacing: 0.5 }}>DELAY RISK</div>
                </div>
              </div>

              {/* Progress bar */}
              <div style={{ marginBottom: 14 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Acquisition Progress</span>
                  <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--teal)' }}>
                    {p.total_parcels > 0 ? Math.round((p.acquired_parcels / p.total_parcels) * 100) : 0}%
                  </span>
                </div>
                <div className="progress-bar">
                  <div
                    className={`progress-fill ${(p.acquired_parcels / (p.total_parcels || 1)) > 0.8 ? 'green' : 'teal'}`}
                    style={{ width: `${p.total_parcels > 0 ? (p.acquired_parcels / p.total_parcels) * 100 : 0}%` }}
                  />
                </div>
              </div>

              {/* Stats row */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, marginBottom: 14 }}>
                {[
                  { label: 'Parcels', value: p.total_parcels },
                  { label: 'Comp Pending', value: p.compensation_pending, color: p.compensation_pending > 0 ? 'var(--saffron)' : 'inherit' },
                  { label: 'Disputes', value: p.disputed_parcels, color: p.disputed_parcels > 0 ? 'var(--red)' : 'inherit' },
                  { label: 'R&R', value: p.rr_pending },
                ].map(s => (
                  <div key={s.label} style={{ textAlign: 'center', padding: '8px 4px', background: 'var(--bg-base)', borderRadius: 8 }}>
                    <div style={{ fontWeight: 700, fontSize: 16, color: s.color || 'var(--text-primary)' }}>{s.value}</div>
                    <div style={{ fontSize: 9, color: 'var(--text-muted)', letterSpacing: 0.3 }}>{s.label}</div>
                  </div>
                ))}
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className={`badge ${p.status}`}>{p.status}</span>
                <span className={`badge ${p.risk_level}`}>{p.risk_level} risk</span>
                <span style={{ fontSize: 11, color: 'var(--teal)', fontWeight: 600 }}>View Details →</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
