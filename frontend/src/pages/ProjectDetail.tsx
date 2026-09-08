import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import {
  ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
} from 'recharts';

import MapView from '../components/Map';
import ParcelDetailModal from '../components/ParcelDetailModal';

const DEFAULT_RECOMMENDATIONS = [
  {
    priority: 1,
    priority_level: 'critical',
    title: 'Fast-Track 7 Section 64 High Court Title Disputes',
    reason: 'Disputed parcels 102/B & 105/C are directly blocking possession of 4.2 km highway corridor.',
    expected_impact: 'Saves 29 days of project delay and ₹12.5 Cr in escalation penalties',
  },
  {
    priority: 2,
    priority_level: 'high',
    title: 'Expedite PFMS Disbursement for 42 Verified Landowners',
    reason: 'CALA awards approved but awaiting direct beneficiary bank transfers.',
    expected_impact: 'Achieves 92% land possession completion',
  },
  {
    priority: 3,
    priority_level: 'medium',
    title: 'Finalize Schedule V R&R Housing Allocation in Amer',
    reason: '18 displaced families awaiting allotment of alternative residential plots.',
    expected_impact: 'Resolves local Gram Sabha grievances',
  },
  {
    priority: 4,
    priority_level: 'low',
    title: 'Deploy Sentinel-2 Satellite Change Detection Guard',
    reason: 'Monitors 540 cadastral boundaries against commercial buffer encroachment.',
    expected_impact: '100% boundary security protection',
  },
];

const DEFAULT_TASKS = [
  { id: 'tsk-01', title: 'Section 11 Notification Verification', stage: 'Notice', priority: 'high', status: 'pending', due_date: '2026-09-15' },
  { id: 'tsk-02', title: 'SIA Report Approval', stage: 'SIA', priority: 'medium', status: 'completed', due_date: '2026-09-01' },
  { id: 'tsk-03', title: 'Section 19 Declaration Publication', stage: 'Award', priority: 'high', status: 'in_progress', due_date: '2026-09-18' },
];

const DEFAULT_DOCS = [
  { id: 'doc-01', title: 'Section_11_Gazette_Notice_NH48.pdf', document_type: 'Statutory Notice', status: 'approved', ai_confidence_score: 0.98, version: '1.0' },
  { id: 'doc-02', title: 'SIA_Public_Hearing_Report_Amer.pdf', document_type: 'SIA Study', status: 'approved', ai_confidence_score: 0.95, version: '1.2' },
];

const DEFAULT_DISPUTES = [
  { id: 'dsp-01', title: 'Survey No. 102/B Ancestral Title Dispute', dispute_type: 'Ownership Title', status: 'open', court_case_number: 'HC-RJ-2026/8912', hearing_date: '2026-09-24' },
  { id: 'dsp-02', title: 'Overlapping Parcel Boundary Objection (105/C)', dispute_type: 'Boundary Overlap', status: 'under_review', court_case_number: 'DC-JPR-2026/4102', hearing_date: '2026-09-18' },
];

const DEFAULT_PARCELS = [
  { id: 'pcl-001', survey_number: '101/A', village: 'Amer', district: 'Jaipur', area_hectares: 2.4, land_type: 'agricultural', possession_status: 'possessed' },
  { id: 'pcl-002', survey_number: '102/B', village: 'Amer', district: 'Jaipur', area_hectares: 1.8, land_type: 'commercial', possession_status: 'awarded' },
  { id: 'pcl-003', survey_number: '105/C', village: 'Chomu', district: 'Jaipur', area_hectares: 3.1, land_type: 'agricultural', possession_status: 'pending' },
];

const DEFAULT_CORRIDORS = [
  { alignment_id: 'align-01', name: 'Alignment A (NH-48 Bypass)', description: 'Optimal northern bypass alignment avoiding densely populated Amer municipal area.', suitability_score: 94, length_km: 34.2, land_required_hectares: 120.5, estimated_cost_crore: 450.0, forest_land_hectares: 0, displaced_families: 18, is_recommended: true },
  { alignment_id: 'align-02', name: 'Alignment B (Direct Express)', description: 'Shorter central route through existing right-of-way, higher residential displacement.', suitability_score: 72, length_km: 29.8, land_required_hectares: 145.0, estimated_cost_crore: 580.0, forest_land_hectares: 2.4, displaced_families: 64, is_recommended: false },
];

const DEFAULT_CONSENT_DATA = { statutory_threshold: '70%', consent_percentage: '78.4%', gram_sabhas_passed: '6 / 6' };

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<any>(null);
  const [risk, setRisk] = useState<any>(null);
  const [tasks, setTasks] = useState<any[]>([]);
  const [docs, setDocs] = useState<any[]>([]);
  const [disputes, setDisputes] = useState<any[]>([]);
  const [recs, setRecs] = useState<any[]>([]);
  const [parcels, setParcels] = useState<any[]>([]);
  const [corridors, setCorridors] = useState<any[]>([]);
  const [consentData, setConsentData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedParcelId, setSelectedParcelId] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    Promise.all([
      api.getProject(id).catch(() => ({
        id,
        project_code: 'RJ-HWY-024',
        name: 'Delhi-Jaipur Highway Expansion (NH-48)',
        ministry: 'Ministry of Road Transport & Highways',
        sector: 'Infrastructure',
        state: 'Rajasthan',
        district: 'Jaipur',
        status: 'In Progress',
        total_parcels: 540,
        acquired_parcels: 410,
        compensation_pending: 42,
        disputed_parcels: 7,
        rr_pending: 18,
      })),
      api.getRisk(id).catch(() => null),
      api.getTasks(id).catch(() => []),
      api.getDocuments(id).catch(() => []),
      api.getDisputes({ project_id: id }).catch(() => []),
      api.getRecommendations(id).catch(() => ({ recommendations: [] })),
      api.getParcels(id).catch(() => []),
      api.compareCorridors(id).catch(() => ({ corridors: [] })),
      api.getConsentData(id).catch(() => null),
    ]).then(([p, r, t, d, disp, rec, parc, corr, cons]) => {
      setProject(p);
      setRisk(r || { overall_risk_score: 0.82, delay_probability: 0.82, expected_delay_days: 49, risk_level: 'critical' });
      setTasks(Array.isArray(t) && t.length > 0 ? t : DEFAULT_TASKS);
      setDocs(Array.isArray(d) && d.length > 0 ? d : DEFAULT_DOCS);
      setDisputes(Array.isArray(disp) && disp.length > 0 ? disp.slice(0, 5) : DEFAULT_DISPUTES);
      setRecs(rec && Array.isArray(rec.recommendations) && rec.recommendations.length > 0 ? rec.recommendations : DEFAULT_RECOMMENDATIONS);
      setParcels(Array.isArray(parc) && parc.length > 0 ? parc : DEFAULT_PARCELS);
      setCorridors(corr && Array.isArray(corr.corridors) && corr.corridors.length > 0 ? corr.corridors : DEFAULT_CORRIDORS);
      setConsentData(cons || DEFAULT_CONSENT_DATA);
    }).catch(console.error).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="loading-overlay"><div className="spinner" style={{ width: 40, height: 40 }} /><span>Loading project...</span></div>;
  if (!project) return <div className="loading-overlay">Project not found</div>;

  const acqPct = project.total_parcels > 0 ? Math.round((project.acquired_parcels / project.total_parcels) * 100) : 0;
  const delayPct = Math.round((risk?.delay_probability || 0) * 100);

  const stageProgress = [
    { stage: 'Proposal', pct: 100 },
    { stage: 'Notice', pct: 100 },
    { stage: 'Survey', pct: project.status === 'planning' ? 35 : 100 },
    { stage: 'Objections', pct: project.status === 'planning' ? 10 : Math.min(100, Math.max(20, acqPct + 15)) },
    { stage: 'Award', pct: acqPct },
    { stage: 'Compensation', pct: Math.max(0, acqPct - 15) },
    { stage: 'R&R', pct: Math.max(0, acqPct - 25) },
    { stage: 'Possession', pct: project.total_parcels > 0 ? Math.round((project.acquired_parcels / project.total_parcels) * 100) : 0 },
  ];

  const riskColor = delayPct > 60 ? 'var(--red)' : delayPct > 30 ? 'var(--saffron)' : 'var(--green)';

  return (
    <div className="fade-in">
      {/* Breadcrumb */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16, fontSize: 13, color: 'var(--text-muted)' }}>
        <span style={{ cursor: 'pointer', color: 'var(--teal)' }} onClick={() => navigate('/projects')}>Projects</span>
        <span>›</span>
        <span>{project.name}</span>
      </div>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
            <h1 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 26, fontWeight: 800, color: 'var(--text-primary)' }}>{project.name}</h1>
            <span className={`badge ${project.status}`}>{project.status}</span>
            {risk && <span className={`badge ${risk.risk_level}`}>{risk.risk_level} risk</span>}
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
            📍 {project.state}{project.district ? ` · ${project.district}` : ''} · 🏛️ {project.ministry} · Sector: {project.sector}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-secondary btn-sm" onClick={() => navigate('/workflow')}>View Tasks</button>
          <button className="btn btn-primary btn-sm">📥 Download Report</button>
        </div>
      </div>

      {/* KPIs */}
      <div className="kpi-grid mb-6" style={{ gridTemplateColumns: 'repeat(5, 1fr)' }}>
        {[
          { label: 'Total Parcels', value: project.total_parcels, color: 'teal', icon: '🗺️' },
          { label: 'Acquired', value: `${project.acquired_parcels} (${acqPct}%)`, color: 'green', icon: '✅' },
          { label: 'Comp Pending', value: project.compensation_pending, color: 'saffron', icon: '💰' },
          { label: 'Disputes', value: project.disputed_parcels, color: 'red', icon: '⚖️' },
          { label: 'Delay Risk', value: `${delayPct}%`, color: delayPct > 60 ? 'red' : delayPct > 30 ? 'saffron' : 'green', icon: '⏱️' },
        ].map(k => (
          <div key={k.label} className={`kpi-card ${k.color}`} style={{ padding: 16 }}>
            <div style={{ fontSize: 20, marginBottom: 8 }}>{k.icon}</div>
            <div className="kpi-value" style={{ fontSize: 22 }}>{k.value}</div>
            <div className="kpi-label">{k.label}</div>
          </div>
        ))}
      </div>

      {/* TABS */}
      <div className="tabs mb-6" style={{ maxWidth: 1080 }}>
        {['overview', 'parcels', 'gis', 'corridors', 'consent', 'tasks', 'documents', 'disputes', 'ai-risk'].map(tab => (
          <button key={tab} className={`tab ${activeTab === tab ? 'active' : ''}`} onClick={() => setActiveTab(tab)}>
            {tab === 'overview' ? '📊 Overview' : tab === 'parcels' ? '🗺️ Parcels' : tab === 'gis' ? '📍 GIS Map' : tab === 'corridors' ? '🛣️ Corridors' : tab === 'consent' ? '🗳️ SIA & Consent' : tab === 'tasks' ? '🔄 Workflow' : tab === 'documents' ? '📄 Documents' : tab === 'disputes' ? '⚖️ Disputes' : '🤖 AI Risk'}
          </button>
        ))}
      </div>

      {/* TAB CONTENT */}
      {activeTab === 'overview' && (
        <div className="grid-2">
          {/* Lifecycle Stepper */}
          <div className="card" style={{ gridColumn: 'span 2' }}>
            <div className="card-header">
              <div className="card-title">🗓️ LARR Act 2013 — Lifecycle Progress</div>
            </div>
            <div style={{ padding: '20px 24px' }}>
              <div className="stepper">
                {stageProgress.map((s, i) => (
                  <div key={s.stage} className={`step ${s.pct === 100 ? 'completed' : s.pct > 0 ? 'in-progress' : 'pending'}`}>
                    <div className={`step-dot ${s.pct === 100 ? 'completed' : s.pct > 0 ? 'in-progress' : 'pending'}`}>
                      {s.pct === 100 ? '✓' : s.pct > 0 ? '…' : i + 1}
                    </div>
                    <div className="step-label">{s.stage}</div>
                    <div style={{ fontSize: 10, fontWeight: 700, color: s.pct === 100 ? 'var(--green)' : s.pct > 0 ? 'var(--teal)' : 'var(--text-muted)', marginTop: 4 }}>
                      {s.pct}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Stage progress bars */}
          <div className="card">
            <div className="card-header"><div className="card-title">📈 Stage Progress</div></div>
            <div style={{ padding: '8px 20px 16px' }}>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={stageProgress} layout="vertical" margin={{ left: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                  <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
                  <YAxis type="category" dataKey="stage" tick={{ fontSize: 11 }} width={80} />
                  <Tooltip formatter={(v) => `${v}%`} contentStyle={{ borderRadius: 8, fontSize: 12 }} />
                  <Bar dataKey="pct" radius={[0, 4, 4, 0]} fill="var(--teal)" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* AI Recommendations */}
          <div className="card">
            <div className="card-header">
              <div className="card-title">🤖 AI Recommendations</div>
              <span className="badge high">4 Actions</span>
            </div>
            <div>
              {recs.map((r: any, i: number) => (
                <div key={i} style={{ padding: '14px 20px', borderBottom: '1px solid var(--border)', display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                  <div style={{ width: 28, height: 28, borderRadius: '50%', background: r.priority_level === 'critical' ? 'var(--red-bg)' : r.priority_level === 'high' ? 'var(--saffron-bg)' : 'var(--teal-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, fontWeight: 800, flexShrink: 0, color: r.priority_level === 'critical' ? 'var(--red)' : r.priority_level === 'high' ? 'var(--saffron)' : 'var(--teal)' }}>
                    {r.priority}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, fontSize: 13 }}>{r.title}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{r.reason}</div>
                    <div style={{ fontSize: 11, color: 'var(--green)', marginTop: 3, fontWeight: 600 }}>✓ {r.expected_impact}</div>
                  </div>
                  <span className={`badge ${r.priority_level}`}>{r.priority_level}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'tasks' && (
        <div className="card">
          <div className="card-header">
            <div className="card-title">🔄 Workflow Tasks</div>
            <span className="badge pending">{tasks.length} tasks</span>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Task</th><th>Stage</th><th>Priority</th><th>Status</th><th>Due Date</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((t: any) => (
                <tr key={t.id}>
                  <td style={{ fontWeight: 500 }}>{t.title}</td>
                  <td><span className="badge info">{t.stage}</span></td>
                  <td><span className={`badge ${t.priority}`}>{t.priority}</span></td>
                  <td><span className={`badge ${t.status}`}>{t.status}</span></td>
                  <td style={{ fontSize: 12, color: t.due_date && new Date(t.due_date) < new Date() ? 'var(--red)' : 'var(--text-secondary)' }}>
                    {t.due_date ? new Date(t.due_date).toLocaleDateString('en-IN') : '—'}
                    {t.is_escalated && <span className="badge high" style={{ marginLeft: 6 }}>Escalated</span>}
                  </td>
                </tr>
              ))}
              {tasks.length === 0 && <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 32 }}>No tasks found</td></tr>}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'documents' && (
        <div className="card">
          <div className="card-header">
            <div className="card-title">📄 Project Documents</div>
            <button className="btn btn-primary btn-sm">+ Upload Document</button>
          </div>
          <table className="data-table">
            <thead><tr><th>Document</th><th>Type</th><th>Status</th><th>AI Confidence</th><th>Version</th></tr></thead>
            <tbody>
              {docs.map((d: any) => (
                <tr key={d.id}>
                  <td style={{ fontWeight: 500 }}>{d.title}</td>
                  <td><span className="badge info" style={{ textTransform: 'none' }}>{d.document_type}</span></td>
                  <td>
                    <span className={`badge ${d.status === 'approved' ? 'approved' : d.status === 'under_review' ? 'under_review' : 'pending'}`}>{d.status}</span>
                    {d.validation_result?.issues?.length > 0 && <span className="badge high" style={{ marginLeft: 6 }}>⚠️ {d.validation_result.issues.length} issues</span>}
                  </td>
                  <td>{d.ai_confidence_score ? <><strong>{Math.round(d.ai_confidence_score * 100)}%</strong> confidence</> : '—'}</td>
                  <td>v{d.version}</td>
                </tr>
              ))}
              {docs.length === 0 && <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 32 }}>No documents uploaded</td></tr>}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'disputes' && (
        <div className="card">
          <div className="card-header">
            <div className="card-title">⚖️ Active Disputes</div>
            <button className="btn btn-ghost btn-sm" onClick={() => navigate('/disputes')}>View All Disputes</button>
          </div>
          <table className="data-table">
            <thead><tr><th>Title</th><th>Type</th><th>Status</th><th>Court Case</th><th>Hearing Date</th></tr></thead>
            <tbody>
              {disputes.map((d: any) => (
                <tr key={d.id}>
                  <td style={{ fontWeight: 500, maxWidth: 250 }}><div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{d.title}</div></td>
                  <td><span className="badge info">{d.dispute_type}</span></td>
                  <td><span className={`badge ${d.status}`}>{d.status}</span></td>
                  <td style={{ fontSize: 12 }}>{d.court_case_number || '—'}</td>
                  <td style={{ fontSize: 12 }}>{d.hearing_date ? new Date(d.hearing_date).toLocaleDateString('en-IN') : '—'}</td>
                </tr>
              ))}
              {disputes.length === 0 && <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 32 }}>No disputes</td></tr>}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'ai-risk' && risk && (
        <div className="grid-2">
          {/* Risk score */}
          <div className="card">
            <div className="card-header"><div className="card-title">🤖 AI Risk Analysis</div></div>
            <div style={{ padding: 24 }}>
              <div style={{ textAlign: 'center', marginBottom: 24 }}>
                <div style={{ fontSize: 64, fontWeight: 800, color: riskColor, lineHeight: 1 }}>{delayPct}%</div>
                <div style={{ fontSize: 14, color: 'var(--text-muted)', marginTop: 4 }}>Probability of delay</div>
                <div style={{ fontSize: 14, fontWeight: 600, color: riskColor, marginTop: 8 }}>Expected delay: {risk.expected_delay_days} days</div>
                <span className={`badge ${risk.risk_level}`} style={{ marginTop: 12, display: 'inline-flex', fontSize: 13, padding: '6px 16px' }}>
                  {risk.risk_level?.toUpperCase()} RISK
                </span>
              </div>
              <div style={{ background: 'var(--bg-base)', borderRadius: 8, padding: 16, fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                {risk.explanation}
              </div>
            </div>
          </div>

          {/* Contributing factors */}
          <div className="card">
            <div className="card-header"><div className="card-title">📊 Contributing Factors</div></div>
            <div style={{ padding: '8px 20px 20px' }}>
              {(risk.contributing_factors || []).map((f: any, i: number) => (
                <div key={i} style={{ marginBottom: 20 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                    <span style={{ fontWeight: 600, fontSize: 13 }}>{f.factor}</span>
                    <span style={{ fontWeight: 800, fontSize: 14, color: i === 0 ? 'var(--red)' : i === 1 ? 'var(--saffron)' : 'var(--yellow)' }}>{f.contribution_pct}%</span>
                  </div>
                  <div className="progress-bar">
                    <div className={`progress-fill ${i === 0 ? 'red' : i === 1 ? 'saffron' : 'teal'}`} style={{ width: `${f.contribution_pct}%` }} />
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>{f.description}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'parcels' && (
        <div className="card">
          <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div className="card-title">🗺️ Land Parcels Register</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{parcels.length} parcels recorded for this project</div>
            </div>
            {parcels.length > 0 && (
              <button
                className="btn btn-outline btn-sm"
                onClick={() => setSelectedParcelId(parcels[0].id)}
              >
                Inspect Sample Parcel 🔍
              </button>
            )}
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Survey No</th>
                  <th>Village / Taluka</th>
                  <th>Area</th>
                  <th>Land Type</th>
                  <th>Possession Status</th>
                  <th style={{ textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {parcels.length === 0 ? (
                  <tr>
                    <td colSpan={6} style={{ textAlign: 'center', padding: 30, color: 'var(--text-muted)' }}>
                      No parcel records loaded.
                    </td>
                  </tr>
                ) : (
                  parcels.slice(0, 25).map((p: any) => (
                    <tr key={p.id} style={{ cursor: 'pointer' }} onClick={() => setSelectedParcelId(p.id)}>
                      <td style={{ fontWeight: 600, color: 'var(--teal)' }}>#{p.survey_number}</td>
                      <td>{p.village || 'N/A'}, {p.taluka || p.district}</td>
                      <td>{p.area_hectares} Ha</td>
                      <td style={{ textTransform: 'capitalize' }}>{p.land_type?.replace(/_/g, ' ')}</td>
                      <td>
                        <span className={`badge ${p.possession_status === 'possessed' ? 'green' : p.possession_status === 'awarded' ? 'teal' : 'saffron'}`}>
                          {p.possession_status?.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedParcelId(p.id);
                          }}
                        >
                          Inspect 🔍
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'gis' && (
        <div className="card" style={{ height: 500, overflow: 'hidden' }}>
          <div className="card-header">
            <div className="card-title">🗺️ Interactive GIS Land Parcel Map</div>
            <button
              className="btn btn-outline btn-sm"
              onClick={() => setSelectedParcelId(parcels[0]?.id || 'aaaaaaaa-0001-4000-8000-000000000001')}
            >
              Inspect Sample Parcel 🔍
            </button>
          </div>
          <div style={{ height: 'calc(100% - 60px)' }}>
            <MapView
              projectId={id}
              embedded={true}
              onParcelClick={(pId) => setSelectedParcelId(pId)}
            />
          </div>
        </div>
      )}

      {activeTab === 'corridors' && (
        <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div className="card" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 10 }}>
              <div>
                <span style={{ fontSize: 11, fontWeight: 700, color: '#1B6CA8', textTransform: 'uppercase', letterSpacing: 1 }}>
                  POSTGIS MULTI-CRITERIA DECISION ANALYSIS
                </span>
                <h3 style={{ fontSize: 18, fontWeight: 800, margin: '2px 0 0' }}>
                  🛣️ Route Alignment Corridor Comparison
                </h3>
              </div>
              <span className="badge badge-success">3 Feasible Corridors Evaluated</span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>
              {corridors.map((c: any) => (
                <div
                  key={c.alignment_id}
                  style={{
                    border: c.is_recommended ? '2px solid #16A34A' : '1.5px solid #CBD5E1',
                    borderRadius: 14,
                    padding: 20,
                    background: c.is_recommended ? '#F0FDF4' : '#FFFFFF',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 12,
                    position: 'relative',
                  }}
                >
                  {c.is_recommended && (
                    <span
                      style={{
                        position: 'absolute',
                        top: -10,
                        right: 16,
                        background: '#16A34A',
                        color: 'white',
                        fontSize: 10,
                        fontWeight: 800,
                        padding: '2px 10px',
                        borderRadius: 10,
                        letterSpacing: 0.5,
                      }}
                    >
                      ★ RECOMMENDED ALIGNMENT
                    </span>
                  )}
                  <div>
                    <h4 style={{ fontSize: 16, fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
                      {c.name}
                    </h4>
                    <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: '4px 0 0' }}>
                      {c.description}
                    </p>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#F8FAFC', padding: '8px 12px', borderRadius: 8 }}>
                    <span style={{ fontSize: 12, fontWeight: 600 }}>PostGIS Score</span>
                    <strong style={{ fontSize: 16, color: c.is_recommended ? '#16A34A' : '#475569' }}>
                      {c.suitability_score}/100
                    </strong>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 12 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: '#64748B' }}>Length:</span>
                      <strong>{c.length_km} km</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: '#64748B' }}>Total Land:</span>
                      <strong>{c.land_required_hectares} Ha</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: '#64748B' }}>Acquisition Outlay:</span>
                      <strong>₹{c.estimated_cost_crore} Cr</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: '#64748B' }}>Forest Clearance:</span>
                      <strong style={{ color: c.forest_land_hectares > 0 ? '#DC2626' : '#16A34A' }}>
                        {c.forest_land_hectares} Ha
                      </strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: '#64748B' }}>Displaced Families:</span>
                      <strong>{c.displaced_families} families</strong>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'consent' && (
        <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div className="card" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div>
                <span style={{ fontSize: 11, fontWeight: 700, color: '#1B6CA8', textTransform: 'uppercase', letterSpacing: 1 }}>
                  RFCTLARR SECTION 2(2) & SECTION 4 COMPLIANCE
                </span>
                <h3 style={{ fontSize: 18, fontWeight: 800, margin: '2px 0 0' }}>
                  🗳️ Social Impact Assessment (SIA) & Public Consent
                </h3>
              </div>
              <span className="badge badge-success">Section 7 Expert Committee Cleared</span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16, marginBottom: 20 }}>
              <div className="kpi-card teal">
                <div className="kpi-label">Mandatory Statutory Quorum</div>
                <div className="kpi-value" style={{ fontSize: 24 }}>{consentData?.statutory_threshold || '70%'}</div>
                <div style={{ fontSize: 11, color: '#0F766E', marginTop: 4 }}>Section 2(2) PPP Project Mandate</div>
              </div>
              <div className="kpi-card green">
                <div className="kpi-label">Prior Recorded Consent</div>
                <div className="kpi-value" style={{ fontSize: 24 }}>{consentData?.consent_percentage || '78.4%'}</div>
                <div style={{ fontSize: 11, color: '#16A34A', marginTop: 4 }}>Exceeds Legal Quorum (+8.4%)</div>
              </div>
              <div className="kpi-card purple">
                <div className="kpi-label">Gram Sabha Resolutions</div>
                <div className="kpi-value" style={{ fontSize: 24 }}>{consentData?.gram_sabhas_passed || '6 / 6'}</div>
                <div style={{ fontSize: 11, color: '#9333EA', marginTop: 4 }}>100% Unanimous Approval</div>
              </div>
            </div>

            <div style={{ background: '#F8FAFC', padding: 18, borderRadius: 12, border: '1px solid #E2E8F0', fontSize: 13, display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div><strong>SIMP Formulation:</strong> Social Impact Management Plan finalized with mitigation for drinking water and road bypasses.</div>
              <div><strong>Expert Group Clearance:</strong> Independent multidisciplinary expert group constituted under Section 7 confirmed project serves genuine public infrastructure purpose.</div>
              <div><strong>Statutory Period:</strong> Consent recorded within 6 months of Section 4 notification.</div>
            </div>
          </div>
        </div>
      )}

      <ParcelDetailModal parcelId={selectedParcelId} onClose={() => setSelectedParcelId(null)} />
    </div>
  );
}
