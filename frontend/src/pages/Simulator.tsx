import { useState } from 'react';
import { api } from '../api/client';

const DEMO_PROJECT_ID = '12345678-1234-5678-1234-567812345678';

export default function Simulator() {
  const [resolveDisputes, setResolveDisputes] = useState(0);
  const [resolveDisputesDays, setResolveDisputesDays] = useState(7);
  const [expediteComp, setExpediteComp] = useState(0);
  const [completeRR, setCompleteRR] = useState(0);
  const [resolveApprovals, setResolveApprovals] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    try {
      const r = await api.simulate({
        project_id: DEMO_PROJECT_ID,
        resolve_disputes: resolveDisputes,
        resolve_disputes_days: resolveDisputesDays,
        expedite_compensation_cases: expediteComp,
        complete_rr_cases: completeRR,
        resolve_approval_delays: resolveApprovals,
      });
      setResult(r);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const riskColor = (pct: number) => pct > 60 ? 'var(--red)' : pct > 30 ? 'var(--saffron)' : 'var(--green)';

  return (
    <div className="fade-in">
      <div className="section-header mb-4">
        <div>
          <div className="section-title">🔬 What-If Scenario Simulator</div>
          <div className="section-subtitle">Model the impact of interventions on project risk and delay — Delhi-Jaipur Highway (RJ-HWY-024)</div>
        </div>
      </div>

      <div className="alert info mb-6">
        <span>ℹ️</span>
        <div>
          This simulator uses AI-calibrated models to estimate the impact of specific interventions on project delay probability and expected timeline. 
          <strong> Results are estimates — not guarantees.</strong>
        </div>
      </div>

      <div className="grid-2">
        {/* Controls */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">⚙️ Configure Interventions</div>
          </div>
          <div style={{ padding: 24 }}>
            {/* Disputes */}
            <div className="slider-group">
              <div className="slider-header">
                <span className="slider-label">🔴 Resolve Disputes</span>
                <span className="slider-value">{resolveDisputes} disputes</span>
              </div>
              <input type="range" className="slider" min={0} max={18} value={resolveDisputes} onChange={e => setResolveDisputes(+e.target.value)} />
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>18 active disputes → Each resolved saves ~1.5 days</div>
            </div>

            {resolveDisputes > 0 && (
              <div className="slider-group">
                <div className="slider-header">
                  <span className="slider-label">⏱️ Resolution Timeline</span>
                  <span className="slider-value">{resolveDisputesDays} days</span>
                </div>
                <input type="range" className="slider" min={1} max={30} value={resolveDisputesDays} onChange={e => setResolveDisputesDays(+e.target.value)} />
              </div>
            )}

            {/* Compensation */}
            <div className="slider-group">
              <div className="slider-header">
                <span className="slider-label">💰 Expedite Compensation</span>
                <span className="slider-value">{expediteComp} cases</span>
              </div>
              <input type="range" className="slider" min={0} max={52} value={expediteComp} onChange={e => setExpediteComp(+e.target.value)} />
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>52 pending cases → Each case saves ~0.8 days</div>
            </div>

            {/* R&R */}
            <div className="slider-group">
              <div className="slider-header">
                <span className="slider-label">👨‍👩‍👧 Complete R&R Cases</span>
                <span className="slider-value">{completeRR} families</span>
              </div>
              <input type="range" className="slider" min={0} max={31} value={completeRR} onChange={e => setCompleteRR(+e.target.value)} />
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>31 R&R pending → Each family saves ~0.5 days</div>
            </div>

            {/* Approval delays */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 0', borderTop: '1px solid var(--border)', marginTop: 8 }}>
              <div>
                <div style={{ fontWeight: 600, fontSize: 13 }}>📋 Resolve Approval Delays</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>5 overdue approvals → saves ~4 days</div>
              </div>
              <button
                onClick={() => setResolveApprovals(!resolveApprovals)}
                style={{
                  width: 44, height: 24, borderRadius: 12, border: 'none', cursor: 'pointer',
                  background: resolveApprovals ? 'var(--teal)' : 'var(--border)',
                  position: 'relative', transition: 'background 0.2s',
                }}
              >
                <span style={{
                  position: 'absolute', top: 2, left: resolveApprovals ? 22 : 2, width: 20, height: 20,
                  borderRadius: '50%', background: 'white', transition: 'left 0.2s',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                }} />
              </button>
            </div>

            <button
              className="btn btn-primary"
              style={{ width: '100%', marginTop: 20 }}
              onClick={run}
              disabled={loading}
            >
              {loading ? <><span className="spinner" />Running Simulation...</> : '▶ Run Simulation'}
            </button>
          </div>
        </div>

        {/* Results */}
        <div>
          {!result ? (
            <div className="card" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 16, minHeight: 400 }}>
              <div style={{ fontSize: 48 }}>🔬</div>
              <div style={{ fontWeight: 600, color: 'var(--text-muted)', textAlign: 'center' }}>
                Configure interventions and run the simulation<br />to see projected impact
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* Current vs Projected */}
              <div className="card">
                <div className="card-header">
                  <div className="card-title">📊 Current vs Projected</div>
                  <span className="badge info">AI Estimate</span>
                </div>
                <div style={{ padding: 24 }}>
                  <div className="grid-2">
                    <div style={{ textAlign: 'center', padding: 20, background: 'var(--red-bg)', borderRadius: 12, border: '1px solid var(--red)' }}>
                      <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--red)', marginBottom: 8, letterSpacing: 0.5 }}>CURRENT</div>
                      <div style={{ fontSize: 48, fontWeight: 900, color: 'var(--red)' }}>{result.current.delay_probability_pct}%</div>
                      <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>delay probability</div>
                      <div style={{ fontSize: 12, color: 'var(--red)', fontWeight: 600, marginTop: 8 }}>{result.current.expected_delay_days} days expected delay</div>
                    </div>
                    <div style={{ textAlign: 'center', padding: 20, background: result.projected.delay_probability_pct < 30 ? 'var(--green-bg)' : 'var(--saffron-bg)', borderRadius: 12, border: `1px solid ${riskColor(result.projected.delay_probability_pct)}` }}>
                      <div style={{ fontSize: 11, fontWeight: 700, color: riskColor(result.projected.delay_probability_pct), marginBottom: 8, letterSpacing: 0.5 }}>PROJECTED</div>
                      <div style={{ fontSize: 48, fontWeight: 900, color: riskColor(result.projected.delay_probability_pct) }}>{result.projected.delay_probability_pct}%</div>
                      <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>delay probability</div>
                      <div style={{ fontSize: 12, color: riskColor(result.projected.delay_probability_pct), fontWeight: 600, marginTop: 8 }}>{result.projected.expected_delay_days} days expected delay</div>
                    </div>
                  </div>

                  {/* Summary */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 20 }}>
                    <div style={{ background: 'var(--green-bg)', borderRadius: 8, padding: 14, textAlign: 'center' }}>
                      <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--green)' }}>-{result.risk_reduction_pct}%</div>
                      <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Risk Reduction</div>
                    </div>
                    <div style={{ background: 'var(--teal-bg)', borderRadius: 8, padding: 14, textAlign: 'center' }}>
                      <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--teal)' }}>{result.days_saved} days</div>
                      <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Estimated Saved</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Interventions */}
              <div className="card">
                <div className="card-header"><div className="card-title">⚡ Intervention Impact</div></div>
                <div>
                  {result.interventions.map((iv: any, i: number) => (
                    <div key={i} style={{ padding: '14px 20px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: 13 }}>{iv.action}</div>
                        <div style={{ fontSize: 12, color: 'var(--green)', fontWeight: 600, marginTop: 2 }}>✓ {iv.impact} · {iv.days_saved} days saved</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div style={{ fontSize: 11, color: 'var(--text-muted)', padding: '0 4px', fontStyle: 'italic' }}>
                ⚠️ {result.disclaimer}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
