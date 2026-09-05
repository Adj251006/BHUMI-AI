import React, { useState } from 'react';
import { api } from '../api/client';

export default function CitizenPortal() {
  const [query, setQuery] = useState('');
  const [lang, setLang] = useState<'en' | 'hi'>('en');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const executeSearch = async (searchTerm: string) => {
    if (!searchTerm.trim()) return;
    setLoading(true);
    setSearched(true);
    try {
      const data = await api.trackParcel(searchTerm.trim());
      setResult(data);
    } catch {
      setResult({ found: false, message: 'Unable to connect to search service. Please try again later.' });
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    executeSearch(query);
  };

  const handleDemoSearch = (demoSurvey: string) => {
    setQuery(demoSurvey);
    executeSearch(demoSurvey);
  };

  // Derive 7-stage lifecycle status for tracker
  const getLifecycleStages = (res: any) => {
    if (!res || !res.parcel) return [];
    const poss = res.parcel.possession_status;
    const comp = res.compensation?.status;

    // Proposal
    const isProposalDone = true;
    // Notification
    const isNotifDone = true;
    // Survey
    const isSurveyDone = poss !== 'not_acquired';
    const isSurveyActive = poss === 'not_acquired';
    // Award
    const isAwardDone = poss === 'awarded' || poss === 'possessed';
    const isAwardActive = poss === 'notice_issued';
    // Compensation
    const isCompDone = comp === 'disbursed';
    const isCompActive = comp === 'pending' || comp === 'under_verification' || poss === 'awarded';
    // R&R
    const isRRActive = isCompActive;
    const isRRDone = poss === 'possessed';
    // Possession
    const isPossDone = poss === 'possessed';

    return [
      { name: lang === 'en' ? 'Proposal' : 'प्रस्ताव', state: isProposalDone ? 'completed' : 'pending' },
      { name: lang === 'en' ? 'Notification' : 'अधिसूचना', state: isNotifDone ? 'completed' : 'pending' },
      { name: lang === 'en' ? 'Survey' : 'सर्वेक्षण', state: isSurveyDone ? 'completed' : isSurveyActive ? 'active' : 'pending' },
      { name: lang === 'en' ? 'Award' : 'अवार्ड', state: isAwardDone ? 'completed' : isAwardActive ? 'active' : 'pending' },
      { name: lang === 'en' ? 'Compensation' : 'मुआवजा', state: isCompDone ? 'completed' : isCompActive ? 'active' : 'pending' },
      { name: lang === 'en' ? 'R&R' : 'पुनर्वास (R&R)', state: isRRDone ? 'completed' : isRRActive ? 'active' : 'pending' },
      { name: lang === 'en' ? 'Possession' : 'कब्जा', state: isPossDone ? 'completed' : 'pending' },
    ];
  };

  const formatCurrency = (amt: number) => {
    if (!amt) return '₹0';
    if (amt >= 10000000) return `₹${(amt / 10000000).toFixed(2)} Cr`;
    if (amt >= 100000) return `₹${(amt / 100000).toFixed(2)} Lakh`;
    return `₹${amt.toLocaleString('en-IN')}`;
  };

  return (
    <div style={{ maxWidth: 860, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* HEADER BANNER */}
      <div
        style={{
          background: 'linear-gradient(135deg, #152F3D, #1B6CA8)',
          color: 'white',
          padding: '28px 32px',
          borderRadius: 16,
          boxShadow: '0 8px 24px rgba(27, 108, 168, 0.2)',
          position: 'relative',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <span style={{ fontSize: 24 }}>👥</span>
              <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1.5, textTransform: 'uppercase', color: '#F39C12' }}>
                {lang === 'en' ? 'NATIONAL CITIZEN PORTAL' : 'राष्ट्रीय नागरिक पोर्टल'}
              </span>
            </div>
            <h1 style={{ fontSize: 24, fontWeight: 800, marginBottom: 6, letterSpacing: '-0.3px' }}>
              {lang === 'en' ? 'Land Acquisition Public Status Tracker' : 'सार्वजनिक भूमि अधिग्रहण स्थिति ट्रैकर'}
            </h1>
            <p style={{ color: '#E2EEF5', fontSize: 13, maxWidth: 560, lineHeight: 1.5 }}>
              {lang === 'en'
                ? 'Check real-time statutory milestones, compensation award status, and possession verification without public PII disclosure.'
                : 'सार्वजनिक व्यक्तिगत पहचान डेटा के बिना रीयल-टाइम वैधानिक स्थिति, मुआवजा और कब्जा स्थिति पारदर्शी रूप से देखें।'}
            </p>
          </div>
          <button
            type="button"
            className="btn btn-sm"
            style={{
              background: 'rgba(255,255,255,0.18)',
              color: 'white',
              border: '1px solid rgba(255,255,255,0.3)',
              borderRadius: 8,
              fontSize: 12,
              fontWeight: 600,
            }}
            onClick={() => setLang(lang === 'en' ? 'hi' : 'en')}
          >
            🌐 {lang === 'en' ? 'हिंदी में देखें' : 'English'}
          </button>
        </div>
      </div>

      {/* SEARCH CARD */}
      <div className="card" style={{ padding: '24px 28px' }}>
        <form onSubmit={handleSearch} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <label style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>
            {lang === 'en' ? 'Enter Survey Number or Parcel Reference' : 'सर्वेक्षण संख्या या पार्सल संदर्भ दर्ज करें'}
            <span style={{ fontWeight: 400, color: 'var(--text-muted)', marginLeft: 8 }}>
              ({lang === 'en' ? 'Example: 100/1' : 'उदाहरण: 100/1'})
            </span>
          </label>

          <div style={{ display: 'flex', gap: 10 }}>
            <input
              id="citizen-survey-input"
              className="form-input"
              style={{
                flex: 1,
                fontSize: 15,
                padding: '11px 16px',
                border: '1.5px solid var(--border-card)',
                borderRadius: 10,
                outline: 'none',
              }}
              placeholder={lang === 'en' ? 'Enter Survey Number (e.g. 100/1)...' : 'खसरा / सर्वेक्षण संख्या दर्ज करें (जैसे 100/1)...'}
              value={query}
              onChange={e => setQuery(e.target.value)}
              required
            />
            <button
              id="citizen-search-btn"
              type="submit"
              className="btn btn-primary"
              style={{ padding: '11px 24px', fontSize: 14, fontWeight: 700, borderRadius: 10 }}
              disabled={loading}
            >
              {loading ? (lang === 'en' ? 'Searching...' : 'खोज रहे हैं...') : (lang === 'en' ? 'Track Status 🔍' : 'स्थिति ट्रैक करें 🔍')}
            </button>
          </div>

          {/* Quick Demo Hint */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              💡 {lang === 'en' ? 'Try demo parcel:' : 'डेमो पार्सल आज़माएँ:'}
            </span>
            {['100/1', '100/8', '100/2'].map(demo => (
              <button
                key={demo}
                type="button"
                id={`demo-parcel-${demo.replace('/', '-')}`}
                onClick={() => handleDemoSearch(demo)}
                style={{
                  background: '#EEF5F8',
                  border: '1px solid #C8DDE6',
                  color: '#1B6CA8',
                  fontSize: 12,
                  fontWeight: 600,
                  padding: '3px 10px',
                  borderRadius: 6,
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.background = '#1B6CA8';
                  e.currentTarget.style.color = '#FFFFFF';
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.background = '#EEF5F8';
                  e.currentTarget.style.color = '#1B6CA8';
                }}
              >
                {demo}
              </button>
            ))}
          </div>
        </form>
      </div>

      {/* RESULTS SECTION */}
      {searched && (
        <div className="card" style={{ padding: '28px', animation: 'fadeIn 0.2s ease-in' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px 20px' }}>
              <div style={{ fontSize: 28, marginBottom: 12 }}>⏳</div>
              <div style={{ color: 'var(--text-muted)', fontSize: 14 }}>
                {lang === 'en' ? 'Retrieving official land acquisition record...' : 'आधिकारिक भूमि अधिग्रहण रिकॉर्ड प्राप्त किया जा रहा है...'}
              </div>
            </div>
          ) : result && result.found ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              {/* STATUS HEADER */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  borderBottom: '1px solid var(--border)',
                  paddingBottom: 20,
                  flexWrap: 'wrap',
                  gap: 12,
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <h2 style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)' }}>
                      {lang === 'en' ? 'Survey No:' : 'सर्वेक्षण सं:'} {result.parcel?.survey_number}
                    </h2>
                    <span
                      style={{
                        background:
                          result.parcel?.possession_status === 'possessed'
                            ? '#E8F8EF'
                            : result.parcel?.possession_status === 'awarded'
                            ? '#FEFAEC'
                            : '#FEF3E2',
                        color:
                          result.parcel?.possession_status === 'possessed'
                            ? '#27AE60'
                            : result.parcel?.possession_status === 'awarded'
                            ? '#D35400'
                            : '#E67E22',
                        fontSize: 11,
                        fontWeight: 700,
                        padding: '3px 10px',
                        borderRadius: 12,
                        textTransform: 'uppercase',
                        letterSpacing: 0.5,
                      }}
                    >
                      {result.parcel?.possession_status?.replace('_', ' ')}
                    </span>
                  </div>
                  <div style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>
                    📍 {result.project?.name} · {result.parcel?.village}, {result.parcel?.district}, {result.parcel?.state}
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                    {lang === 'en' ? 'Sponsoring Ministry' : 'प्रायोजक मंत्रालय'}
                  </div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginTop: 2 }}>
                    {result.project?.ministry}
                  </div>
                </div>
              </div>

              {/* 7-STAGE LIFECYCLE TRACKER */}
              <div>
                <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 14 }}>
                  {lang === 'en' ? 'Statutory Acquisition Progress' : 'वैधानिक अधिग्रहण प्रगति'}
                </div>
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(7, 1fr)',
                    gap: 8,
                    background: '#F8FAFC',
                    padding: '16px 12px',
                    borderRadius: 12,
                    border: '1px solid #E2E8F0',
                  }}
                >
                  {getLifecycleStages(result).map((stage, idx) => {
                    const isDone = stage.state === 'completed';
                    const isActive = stage.state === 'active';

                    return (
                      <div key={idx} style={{ textAlign: 'center' }}>
                        <div
                          style={{
                            width: 32,
                            height: 32,
                            borderRadius: '50%',
                            margin: '0 auto 8px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: 13,
                            fontWeight: 700,
                            background: isDone ? '#27AE60' : isActive ? '#F39C12' : '#CBD5E1',
                            color: '#FFFFFF',
                            boxShadow: isActive ? '0 0 0 4px #FEF3E2' : 'none',
                          }}
                        >
                          {isDone ? '✓' : isActive ? '●' : '○'}
                        </div>
                        <div
                          style={{
                            fontSize: 11,
                            fontWeight: isActive || isDone ? 700 : 500,
                            color: isDone ? '#27AE60' : isActive ? '#D35400' : '#64748B',
                            lineHeight: 1.2,
                          }}
                        >
                          {stage.name}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* PARCEL & COMPENSATION DETAILS GRID */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: 16,
                  background: '#FFFFFF',
                  border: '1px solid #E2E8F0',
                  borderRadius: 12,
                  padding: 20,
                }}
              >
                <div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                    {lang === 'en' ? 'Land Area' : 'भूमि का क्षेत्रफल'}
                  </div>
                  <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', marginTop: 2 }}>
                    {result.parcel?.area_hectares} Hectares
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                    {lang === 'en' ? 'Land Classification' : 'भूमि वर्गीकरण'}
                  </div>
                  <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', marginTop: 2, textTransform: 'capitalize' }}>
                    {result.parcel?.land_type || 'Agricultural'}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                    {lang === 'en' ? 'Award Compensation' : 'निर्धारित मुआवजा'}
                  </div>
                  <div style={{ fontSize: 16, fontWeight: 700, color: '#1B6CA8', marginTop: 2 }}>
                    {result.compensation?.assessed_amount
                      ? formatCurrency(result.compensation.assessed_amount)
                      : 'Under Assessment'}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                    {lang === 'en' ? 'Disbursement Status' : 'वितरण की स्थिति'}
                  </div>
                  <div
                    style={{
                      fontSize: 14,
                      fontWeight: 700,
                      color: result.compensation?.status === 'disbursed' ? '#27AE60' : '#E67E22',
                      marginTop: 2,
                      textTransform: 'capitalize',
                    }}
                  >
                    {result.compensation?.status || 'Pending Verification'}
                  </div>
                </div>
              </div>

              {/* STATUTORY NOTICE & CITIZEN GUIDANCE */}
              <div
                style={{
                  background: '#F0F9FF',
                  border: '1px solid #BAE6FD',
                  borderRadius: 10,
                  padding: '14px 18px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                }}
              >
                <span style={{ fontSize: 20 }}>ℹ️</span>
                <div style={{ fontSize: 12, color: '#0369A1', lineHeight: 1.5 }}>
                  <strong>{lang === 'en' ? 'Public Transparency Notice: ' : 'सार्वजनिक पारदर्शिता सूचना: '}</strong>
                  {lang === 'en'
                    ? 'In compliance with statutory privacy regulations under the Digital Personal Data Protection Act, individual beneficiary account identifiers and Aadhaar records are protected and only accessible at the CALA District Collector office.'
                    : 'डिजिटल व्यक्तिगत डेटा संरक्षण अधिनियम के अनुपालन में, व्यक्तिगत बैंक खाता विवरण और आधार रिकॉर्ड केवल सक्षम प्राधिकारी (CALA) कार्यालय में सत्यापन योग्य हैं।'}
                </div>
              </div>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '32px 20px' }}>
              <div style={{ fontSize: 32, marginBottom: 12 }}>🔍</div>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 6 }}>
                {lang === 'en' ? 'No Matching Parcel Record Found' : 'कोई मेल खाता पार्सल रिकॉर्ड नहीं मिला'}
              </h3>
              <p style={{ color: 'var(--text-muted)', fontSize: 13, maxWidth: 440, margin: '0 auto 16px' }}>
                {result?.message || 'Please check your survey number or parcel reference. Ensure the format matches the revenue record.'}
              </p>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => handleDemoSearch('100/1')}
              >
                {lang === 'en' ? 'Load Demo Parcel 100/1' : 'डेमो पार्सल 100/1 लोड करें'}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
