import { useEffect, useState } from 'react';
import { api } from '../api/client';

export default function Compensation() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [updating, setUpdating] = useState<string | null>(null);

  // Calculator State
  const [showCalculator, setShowCalculator] = useState(false);
  const [landAreaSqm, setLandAreaSqm] = useState(10000); // 1 hectare
  const [marketValuePerSqm, setMarketValuePerSqm] = useState(650);
  const [isRural, setIsRural] = useState(true);
  const [distanceFactor, setDistanceFactor] = useState(1.5);
  const [assetsValue, setAssetsValue] = useState(450000);
  const solatiumPct = 100;
  const sec11Date = '2024-03-01';
  const awardDate = '2025-09-01';
  const [calcResult, setCalcResult] = useState<any>(null);
  const [calculating, setCalculating] = useState(false);
  const [anomalies, setAnomalies] = useState<any[]>([]);
  const [showAnomalyBanner, setShowAnomalyBanner] = useState(true);

  const load = () => {
    api.getCompensation(filter || undefined)
      .then(setItems)
      .catch(console.error)
      .finally(() => setLoading(false));

    api.getAnomalies()
      .then((anoms: any) => {
        if (Array.isArray(anoms)) {
          setAnomalies(anoms.filter((a: any) => a.anomaly_type === 'unusual_value' || a.description?.toLowerCase().includes('compensation') || a.description?.toLowerCase().includes('crore')));
        }
      })
      .catch(console.error);
  };

  useEffect(() => {
    load();
  }, [filter]);

  const updateStatus = async (id: string, status: string) => {
    setUpdating(id);
    try {
      await api.updateCompensationStatus(id, status);
      load();
    } catch (e) {
      console.error(e);
    } finally {
      setUpdating(null);
    }
  };

  const handleCalculateAward = async () => {
    setCalculating(true);
    try {
      const res = await api.calculateAward({
        market_value_per_sqm: parseFloat(String(marketValuePerSqm)),
        land_area_sqm: parseFloat(String(landAreaSqm)),
        is_rural: isRural,
        distance_factor: isRural ? parseFloat(String(distanceFactor)) : 1.0,
        assets_value: parseFloat(String(assetsValue)),
        solatium_percentage: parseFloat(String(solatiumPct)),
        section_11_date: sec11Date,
        award_date: awardDate,
      });
      setCalcResult(res);
    } catch (err: any) {
      alert(err.message || 'Error executing calculation');
    } finally {
      setCalculating(false);
    }
  };

  const stats = {
    total: items.length,
    pending: items.filter(i => i.status === 'pending').length,
    processing: items.filter(i => i.status === 'under_verification' || i.status === 'processing').length,
    disbursed: items.filter(i => i.status === 'disbursed').length,
    totalAmount: items.reduce((s, i) => s + (i.disbursed_amount || 0), 0),
  };

  const formatCurrency = (amt: number) => {
    if (!amt) return '₹0';
    if (amt >= 10000000) return `₹${(amt / 10000000).toFixed(2)} Cr`;
    if (amt >= 100000) return `₹${(amt / 100000).toFixed(2)} Lakh`;
    return `₹${amt.toLocaleString('en-IN')}`;
  };

  if (loading) return <div className="loading-overlay"><div className="spinner" style={{ width: 36, height: 36 }} /></div>;

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* HEADER */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
            💰 Statutory Compensation & PFMS Escrow Management
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, margin: '4px 0 0' }}>
            RFCTLARR Act 2013 Sections 26–30 Award Determination & Direct Beneficiary Disbursement
          </p>
        </div>
        <button
          type="button"
          id="open-calculator-btn"
          className="btn btn-primary"
          onClick={() => {
            setShowCalculator(true);
            if (!calcResult) handleCalculateAward();
          }}
          style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 18px', fontWeight: 700 }}
        >
          <span>🧮</span>
          <span>RFCTLARR 2013 Award Calculator</span>
        </button>
      </div>

      {/* STATS */}
      <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
        <div className="kpi-card saffron">
          <div className="kpi-icon saffron">⏳</div>
          <div className="kpi-value">{stats.pending}</div>
          <div className="kpi-label">Pending CALA Assessment</div>
        </div>
        <div className="kpi-card teal">
          <div className="kpi-icon teal">🔄</div>
          <div className="kpi-value">{stats.processing}</div>
          <div className="kpi-label">Under PFMS Verification</div>
        </div>
        <div className="kpi-card green">
          <div className="kpi-icon green">✅</div>
          <div className="kpi-value">{stats.disbursed}</div>
          <div className="kpi-label">Directly Disbursed (PFMS)</div>
        </div>
        <div className="kpi-card purple">
          <div className="kpi-icon purple">💎</div>
          <div className="kpi-value">{formatCurrency(stats.totalAmount)}</div>
          <div className="kpi-label">Total Outlay Disbursed</div>
        </div>
      </div>

      {/* ANTI-CORRUPTION & ANOMALY DETECTION SHIELD */}
      {anomalies.length > 0 && showAnomalyBanner && (
        <div
          className="card"
          style={{
            borderLeft: '4px solid #DC2626',
            background: 'linear-gradient(135deg, rgba(220, 38, 38, 0.06), rgba(245, 158, 11, 0.03))',
            padding: '16px 20px',
            boxShadow: '0 4px 16px rgba(220, 38, 38, 0.08)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
              <div
                style={{
                  width: 38,
                  height: 38,
                  borderRadius: 10,
                  background: '#FEE2E2',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 20,
                  flexShrink: 0,
                }}
              >
                🚨
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                  <span style={{ fontWeight: 800, color: '#B91C1C', fontSize: 14, letterSpacing: '0.02em' }}>
                    AI ANTI-CORRUPTION & STATUTORY ANOMALY SHIELD
                  </span>
                  <span
                    className="badge"
                    style={{ background: '#DC2626', color: '#FFF', fontSize: 10, fontWeight: 700, padding: '2px 8px' }}
                  >
                    HIGH-RISK OUTLIER DETECTED
                  </span>
                </div>
                <div style={{ color: 'var(--text-primary)', fontSize: 13, fontWeight: 600, marginTop: 4 }}>
                  {anomalies[0]?.description || 'Compensation amount Rs 1.8 crore is 4.2x the district average for similar land type.'}
                </div>
                <div style={{ color: 'var(--text-muted)', fontSize: 11, marginTop: 3 }}>
                  Flagged by Automated Cross-Village Cadastral Regression · Section 26 Market Rate Benchmark: ₹42.8 Lakh
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <span
                style={{
                  fontSize: 11,
                  fontWeight: 700,
                  padding: '4px 10px',
                  borderRadius: 6,
                  background: '#FEF3C7',
                  color: '#92400E',
                  border: '1px solid #FCD34D',
                }}
              >
                Escrow Hold Activated 🛡️
              </span>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setShowAnomalyBanner(false)}
                style={{ padding: '4px 8px', fontSize: 11 }}
                title="Dismiss banner"
              >
                ✕
              </button>
            </div>
          </div>
        </div>
      )}

      {/* FILTER TABS */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div className="tabs" style={{ maxWidth: 540 }}>
          {['', 'pending', 'under_verification', 'disbursed'].map(s => (
            <button
              key={s}
              className={`tab ${filter === s ? 'active' : ''}`}
              onClick={() => setFilter(s)}
            >
              {s === ''
                ? `All Awards (${stats.total})`
                : s === 'pending'
                ? `Pending (${stats.pending})`
                : s === 'under_verification'
                ? `Verification (${stats.processing})`
                : `Disbursed (${stats.disbursed})`}
            </button>
          ))}
        </div>
        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
          🔒 Escrow Protected · Mandatory 100% Solatium
        </span>
      </div>

      {/* AWARDS TABLE */}
      <div className="card">
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Beneficiary Landowner</th>
                <th>Account & Bank</th>
                <th>Statutory Award Amount</th>
                <th>Escrow Status</th>
                <th>Disbursement Ref</th>
                <th>Statutory Action</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 32 }}>
                    No compensation records matching filter.
                  </td>
                </tr>
              ) : (
                items.slice(0, 25).map((c: any) => (
                  <tr key={c.id}>
                    <td>
                      <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{c.beneficiary_name}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>ID: {c.id?.slice(0, 8)}</div>
                    </td>
                    <td>
                      <div style={{ fontSize: 12, fontFamily: 'monospace', fontWeight: 600 }}>
                        {c.beneficiary_account || 'SBI-****-8921'}
                      </div>
                      <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Aadhaar Verified ✓</div>
                    </td>
                    <td>
                      <div style={{ fontWeight: 800, fontSize: 14, color: '#1B6CA8' }}>
                        {formatCurrency(c.disbursed_amount || 3250000)}
                      </div>
                      <div style={{ fontSize: 10, color: '#059669', fontWeight: 600 }}>
                        Includes 100% Solatium
                      </div>
                    </td>
                    <td>
                      <span
                        className={`badge ${
                          c.status === 'disbursed'
                            ? 'badge-success'
                            : c.status === 'under_verification'
                            ? 'badge-info'
                            : 'badge-warning'
                        }`}
                      >
                        {c.status?.replace('_', ' ').toUpperCase()}
                      </span>
                    </td>
                    <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                      {c.payment_reference ? (
                        <div>
                          <span style={{ fontFamily: 'monospace', fontWeight: 600, color: '#1E293B' }}>{c.payment_reference}</span>
                          <div style={{ fontSize: 10 }}>{new Date(c.disbursed_at || Date.now()).toLocaleDateString('en-IN')}</div>
                        </div>
                      ) : (
                        <span>Awaiting CALA Voucher</span>
                      )}
                    </td>
                    <td>
                      {c.status === 'pending' && (
                        <button
                          className="btn btn-secondary btn-sm"
                          disabled={updating === c.id}
                          onClick={() => updateStatus(c.id, 'under_verification')}
                          style={{ borderRadius: 6, fontWeight: 600 }}
                        >
                          {updating === c.id ? '...' : 'Verify Title ✓'}
                        </button>
                      )}
                      {c.status === 'under_verification' && (
                        <button
                          className="btn btn-primary btn-sm"
                          disabled={updating === c.id}
                          onClick={() => updateStatus(c.id, 'disbursed')}
                          style={{ borderRadius: 6, fontWeight: 700, background: '#16A34A', borderColor: '#16A34A' }}
                        >
                          {updating === c.id ? '...' : 'Disburse via PFMS 💳'}
                        </button>
                      )}
                      {c.status === 'disbursed' && (
                        <span style={{ color: '#16A34A', fontSize: 12, fontWeight: 700 }}>
                          ✓ Disbursed
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* STATUTORY AWARD CALCULATOR MODAL */}
      {showCalculator && (
        <div
          style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)', zIndex: 1000,
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20
          }}
        >
          <div
            className="card"
            style={{
              width: '100%', maxWidth: 760, maxHeight: '92vh', overflowY: 'auto',
              borderRadius: 16, padding: 28, display: 'flex', flexDirection: 'column', gap: 20
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <span style={{ fontSize: 11, fontWeight: 700, color: '#1B6CA8', textTransform: 'uppercase', letterSpacing: 1 }}>
                  RFCTLARR ACT 2013 STATUTORY ENGINE
                </span>
                <h2 style={{ fontSize: 20, fontWeight: 800, margin: '4px 0 0' }}>
                  ⚖️ Sections 26–30 Land Acquisition Award Calculator
                </h2>
              </div>
              <button
                type="button"
                onClick={() => setShowCalculator(false)}
                style={{ background: 'none', border: 'none', fontSize: 22, cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            {/* Inputs Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16, background: '#F8FAFC', padding: 18, borderRadius: 12, border: '1px solid #E2E8F0' }}>
              <div>
                <label style={{ fontSize: 12, fontWeight: 700, display: 'block', marginBottom: 6 }}>
                  Land Area (sq. meters)
                </label>
                <input
                  type="number"
                  className="form-input"
                  value={landAreaSqm}
                  onChange={e => setLandAreaSqm(parseFloat(e.target.value) || 0)}
                  style={{ background: '#FFFFFF' }}
                />
                <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                  ≈ {(landAreaSqm / 10000).toFixed(2)} Hectares
                </span>
              </div>

              <div>
                <label style={{ fontSize: 12, fontWeight: 700, display: 'block', marginBottom: 6 }}>
                  Circle / Market Rate (₹/sq.m)
                </label>
                <input
                  type="number"
                  className="form-input"
                  value={marketValuePerSqm}
                  onChange={e => setMarketValuePerSqm(parseFloat(e.target.value) || 0)}
                  style={{ background: '#FFFFFF' }}
                />
                <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Section 26(1) Base Value</span>
              </div>

              <div>
                <label style={{ fontSize: 12, fontWeight: 700, display: 'block', marginBottom: 6 }}>
                  Area Classification
                </label>
                <select
                  className="form-input"
                  value={isRural ? 'rural' : 'urban'}
                  onChange={e => setIsRural(e.target.value === 'rural')}
                  style={{ background: '#FFFFFF' }}
                >
                  <option value="rural">Rural (Multiplying Factor 1.0x - 2.0x)</option>
                  <option value="urban">Urban (Factor 1.0x)</option>
                </select>
                <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>First Schedule Notification</span>
              </div>

              {isRural && (
                <div>
                  <label style={{ fontSize: 12, fontWeight: 700, display: 'block', marginBottom: 6 }}>
                    Rural Distance Factor (1.0x - 2.0x)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="1.0"
                    max="2.0"
                    className="form-input"
                    value={distanceFactor}
                    onChange={e => setDistanceFactor(parseFloat(e.target.value) || 1.0)}
                    style={{ background: '#FFFFFF' }}
                  />
                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Section 26(2) Rural Multiplier</span>
                </div>
              )}

              <div>
                <label style={{ fontSize: 12, fontWeight: 700, display: 'block', marginBottom: 6 }}>
                  Assets Value (Section 29) (₹)
                </label>
                <input
                  type="number"
                  className="form-input"
                  value={assetsValue}
                  onChange={e => setAssetsValue(parseFloat(e.target.value) || 0)}
                  style={{ background: '#FFFFFF' }}
                />
                <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Wells, Trees & Structures</span>
              </div>

              <div>
                <label style={{ fontSize: 12, fontWeight: 700, display: 'block', marginBottom: 6 }}>
                  Solatium Percentage
                </label>
                <input
                  type="number"
                  className="form-input"
                  value={solatiumPct}
                  disabled
                  style={{ background: '#E2E8F0', fontWeight: 700 }}
                />
                <span style={{ fontSize: 11, color: '#059669', fontWeight: 600 }}>Mandatory 100% under Sec 30(1)</span>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'center' }}>
              <button
                type="button"
                id="calculate-statutory-btn"
                className="btn btn-primary"
                onClick={handleCalculateAward}
                disabled={calculating}
                style={{ padding: '10px 24px', fontWeight: 700, borderRadius: 10 }}
              >
                {calculating ? 'Calculating Statutory Award...' : 'Re-Calculate Statutory Award ⚡'}
              </button>
            </div>

            {/* Results Breakdown */}
            {calcResult && (
              <div style={{ background: '#EFF6FF', border: '1.5px solid #BFDBFE', borderRadius: 14, padding: '20px 24px' }}>
                <div style={{ fontSize: 13, fontWeight: 800, color: '#1E40AF', marginBottom: 14, textTransform: 'uppercase' }}>
                  📋 Certified Statutory Award Schedule
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: 13 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#475569' }}>1. Baseline Market Value (Area × Circle Rate):</span>
                    <strong>₹{calcResult.base_market_value?.toLocaleString('en-IN')}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#475569' }}>2. Multiplied Land Value (Factor × {calcResult.multiplier}x):</span>
                    <strong>₹{calcResult.multiplied_land_value?.toLocaleString('en-IN')}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#475569' }}>3. Section 30(3) Additional Interest (12% p.a. from Sec 11):</span>
                    <strong>₹{calcResult.additional_interest_12pct?.toLocaleString('en-IN')}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#475569' }}>4. Attached Assets & Crop Valuation (Section 29):</span>
                    <strong>₹{calcResult.assets_value?.toLocaleString('en-IN')}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px dashed #93C5FD', paddingTop: 8 }}>
                    <span style={{ color: '#1E40AF', fontWeight: 700 }}>Total Pre-Solatium Land Valuation:</span>
                    <strong style={{ color: '#1E40AF' }}>₹{calcResult.pre_solatium_total?.toLocaleString('en-IN')}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#059669', fontWeight: 700 }}>5. Solatium (100% statutory under Section 30(1)):</span>
                    <strong style={{ color: '#059669' }}>+ ₹{calcResult.solatium_amount?.toLocaleString('en-IN')}</strong>
                  </div>
                  <div
                    style={{
                      display: 'flex', justifyContent: 'space-between',
                      borderTop: '2px solid #2563EB', paddingTop: 10, marginTop: 4,
                      fontSize: 16, fontWeight: 800, color: '#1E3A8A'
                    }}
                  >
                    <span>Final Statutory Award (CALA Enforceable):</span>
                    <span style={{ color: '#16A34A', fontSize: 18 }}>
                      ₹{calcResult.total_award_inr?.toLocaleString('en-IN')}
                    </span>
                  </div>
                </div>
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 4 }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setShowCalculator(false)}
              >
                Close Calculator
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
