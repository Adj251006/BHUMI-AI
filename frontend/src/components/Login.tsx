import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface DemoCred {
  label: string;
  role: string;
  email: string;
  password: string;
  color: string;
  desc: string;
  targetView: string;
}

const DEMO_CREDS: DemoCred[] = [
  {
    label: '🏛️ Central Admin',
    role: 'Central Ministry',
    email: 'admin@mord.gov.in',
    password: 'admin123',
    color: '#1B6CA8',
    desc: 'Full national command center',
    targetView: 'National Dashboard',
  },
  {
    label: '🏛️ State Admin',
    role: 'State Govt (RJ)',
    email: 'rajasthan@gov.in',
    password: 'state123',
    color: '#27AE60',
    desc: 'Rajasthan state-wide oversight',
    targetView: 'State Dashboard',
  },
  {
    label: '🏢 District Officer',
    role: 'District Collector',
    email: 'jaipur@gov.in',
    password: 'district123',
    color: '#8E44AD',
    desc: 'Jaipur district acquisition',
    targetView: 'District Projects',
  },
  {
    label: '🏗️ Project Agency',
    role: 'NHAI Manager',
    email: 'rj-hwy@nhia.in',
    password: 'project123',
    color: '#E67E22',
    desc: 'Delhi-Jaipur Highway execution',
    targetView: 'Project Detail',
  },
  {
    label: '📍 Field Officer',
    role: 'Inspection Officer',
    email: 'field.rahul@gov.in',
    password: 'field123',
    color: '#16A085',
    desc: 'On-ground GPS verification',
    targetView: 'Field Portal',
  },
  {
    label: '🔒 Auditor',
    role: 'Statutory Auditor',
    email: 'auditor@mord.gov.in',
    password: 'audit123',
    color: '#C0392B',
    desc: 'Tamper-evident audit logs',
    targetView: 'Audit Trail',
  },
];

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeQuickLogin, setActiveQuickLogin] = useState<string | null>(null);
  const [error, setError] = useState('');

  const handleRedirectForUser = (loggedUser: any) => {
    if (loggedUser.role === 'field_officer') {
      navigate('/field');
    } else if (loggedUser.role === 'citizen') {
      navigate('/citizen');
    } else if (loggedUser.role === 'state_govt') {
      navigate(loggedUser.state ? `/state/${encodeURIComponent(loggedUser.state)}` : '/dashboard');
    } else if (loggedUser.role === 'district_authority') {
      navigate('/projects');
    } else if (loggedUser.role === 'project_agency') {
      navigate('/project/12345678-1234-5678-1234-567812345678');
    } else if (loggedUser.role === 'auditor') {
      navigate('/audit');
    } else {
      navigate('/dashboard');
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const loggedUser = await login(email, password);
      handleRedirectForUser(loggedUser);
    } catch (err: any) {
      setError(err.message || 'Login failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  // Option B: 1-Click Instant Demo Authentication
  const handleQuickLogin = async (cred: DemoCred) => {
    setEmail(cred.email);
    setPassword(cred.password);
    setActiveQuickLogin(cred.email);
    setLoading(true);
    setError('');
    try {
      const loggedUser = await login(cred.email, cred.password);
      handleRedirectForUser(loggedUser);
    } catch (err: any) {
      setError(err.message || 'Instant login failed. Please retry.');
    } finally {
      setLoading(false);
      setActiveQuickLogin(null);
    }
  };

  return (
    <div className="login-page">
      {/* LEFT — 60% Branding Panel */}
      <div className="login-left">
        <div style={{ position: 'relative', zIndex: 1, maxWidth: 620, width: '100%' }}>
          {/* Logo & National Badge */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 40 }}>
            <div
              style={{
                width: 60,
                height: 60,
                borderRadius: 16,
                background: 'linear-gradient(135deg, #FF9933 0%, #E67E22 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 30,
                boxShadow: '0 10px 25px rgba(230,126,34,0.4)',
                border: '1px solid rgba(255,255,255,0.2)',
              }}
            >
              🌱
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <h1
                  style={{
                    fontFamily: "'Space Grotesk', sans-serif",
                    fontSize: 34,
                    fontWeight: 800,
                    color: '#FFFFFF',
                    letterSpacing: '-0.5px',
                    lineHeight: 1,
                    margin: 0,
                  }}
                >
                  BHUMI-AI
                </h1>
                <span
                  style={{
                    background: 'rgba(255, 153, 51, 0.2)',
                    color: '#FFB870',
                    border: '1px solid rgba(255, 153, 51, 0.4)',
                    borderRadius: 20,
                    padding: '3px 9px',
                    fontSize: 10,
                    fontWeight: 700,
                    letterSpacing: 0.5,
                  }}
                >
                  SIH 2026
                </span>
              </div>
              <p
                style={{
                  color: '#89C4E0',
                  fontSize: 11,
                  fontWeight: 600,
                  letterSpacing: 1.2,
                  marginTop: 6,
                  textTransform: 'uppercase',
                }}
              >
                Intelligent National Land Acquisition Platform
              </p>
            </div>
          </div>

          <h2
            style={{
              fontFamily: "'Space Grotesk', sans-serif",
              fontSize: 42,
              fontWeight: 800,
              color: '#FFFFFF',
              lineHeight: 1.2,
              marginBottom: 18,
            }}
          >
            From Land Acquisition<br />
            <span style={{ color: '#FF9933' }}>to Intelligent</span><br />
            Decision Support.
          </h2>

          <p
            style={{
              color: '#B0D3E5',
              fontSize: 15,
              lineHeight: 1.7,
              marginBottom: 36,
              maxWidth: 540,
            }}
          >
            Observe, Understand, Predict, Recommend, and Act. Centralized digital monitoring and real-time AI decision
            support for national infrastructure, highway, and industrial corridors under the RFCTLARR Act 2013.
          </p>

          {/* Feature Badges Grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: 10,
              marginBottom: 44,
              maxWidth: 540,
            }}
          >
            {[
              { icon: '🗺️', label: 'Real-Time PostGIS' },
              { icon: '🤖', label: 'Predictive Risk Engine' },
              { icon: '💰', label: 'PFMS Direct Benefit' },
              { icon: '⚖️', label: 'Dispute Resolution' },
              { icon: '📄', label: 'Document Intelligence' },
              { icon: '🔒', label: 'Audit Trail Security' },
            ].map((f) => (
              <div
                key={f.label}
                style={{
                  background: 'rgba(255, 255, 255, 0.07)',
                  border: '1px solid rgba(255, 255, 255, 0.12)',
                  borderRadius: 8,
                  padding: '9px 12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <span style={{ fontSize: 16 }}>{f.icon}</span>
                <span style={{ color: '#E2EEF5', fontSize: 12, fontWeight: 500 }}>{f.label}</span>
              </div>
            ))}
          </div>

          {/* Key National Metrics */}
          <div
            style={{
              display: 'flex',
              gap: 48,
              borderTop: '1px solid rgba(255, 255, 255, 0.12)',
              paddingTop: 28,
            }}
          >
            {[
              { value: '28', label: 'States Connected' },
              { value: '₹2,400Cr', label: 'Awards Monitored' },
              { value: '15,000+', label: 'Parcels Geo-tagged' },
            ].map((s) => (
              <div key={s.label}>
                <div
                  style={{
                    fontFamily: "'Space Grotesk', sans-serif",
                    fontSize: 26,
                    fontWeight: 800,
                    color: '#FF9933',
                  }}
                >
                  {s.value}
                </div>
                <div style={{ color: '#89C4E0', fontSize: 12, marginTop: 2 }}>{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* RIGHT — 40% Authentication & Demo Section */}
      <div className="login-right">
        <div style={{ width: '100%', maxWidth: 460 }}>
          {/* Header Title */}
          <div style={{ marginBottom: 24 }}>
            <h2
              style={{
                fontSize: 26,
                fontWeight: 800,
                color: '#0F172A',
                marginBottom: 6,
                fontFamily: "'Space Grotesk', sans-serif",
              }}
            >
              Sign In to Portal
            </h2>
            <p style={{ color: '#64748B', fontSize: 14, margin: 0 }}>
              Access the National Land Acquisition & Management System
            </p>
          </div>

          {error && (
            <div
              className="alert high"
              style={{
                marginBottom: 20,
                background: '#FEF2F2',
                border: '1px solid #FCA5A5',
                color: '#991B1B',
                borderRadius: 8,
                padding: '10px 14px',
                fontSize: 13,
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <span>⚠️</span>
              <span>{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleLogin}>
            <div className="form-group" style={{ marginBottom: 16 }}>
              <label
                style={{
                  display: 'block',
                  fontSize: 13,
                  fontWeight: 600,
                  color: '#334155',
                  marginBottom: 6,
                }}
              >
                Government Email / Username
              </label>
              <input
                type="email"
                className="form-control"
                placeholder="officer@gov.in"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                style={{
                  width: '100%',
                  padding: '11px 14px',
                  borderRadius: 8,
                  border: '1.5px solid #CBD5E1',
                  fontSize: 14,
                  color: '#0F172A',
                  background: '#FFFFFF',
                  outline: 'none',
                  transition: 'border-color 0.15s, box-shadow 0.15s',
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = '#1B6CA8';
                  e.currentTarget.style.boxShadow = '0 0 0 3px rgba(27, 108, 168, 0.15)';
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = '#CBD5E1';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              />
            </div>

            <div className="form-group" style={{ marginBottom: 20 }}>
              <label
                style={{
                  display: 'block',
                  fontSize: 13,
                  fontWeight: 600,
                  color: '#334155',
                  marginBottom: 6,
                }}
              >
                Password
              </label>
              <input
                type="password"
                className="form-control"
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                style={{
                  width: '100%',
                  padding: '11px 14px',
                  borderRadius: 8,
                  border: '1.5px solid #CBD5E1',
                  fontSize: 14,
                  color: '#0F172A',
                  background: '#FFFFFF',
                  outline: 'none',
                  transition: 'border-color 0.15s, box-shadow 0.15s',
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = '#1B6CA8';
                  e.currentTarget.style.boxShadow = '0 0 0 3px rgba(27, 108, 168, 0.15)';
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = '#CBD5E1';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{
                width: '100%',
                padding: '12px',
                fontSize: 14,
                fontWeight: 700,
                borderRadius: 8,
                background: '#072F37',
                border: 'none',
                color: '#FFFFFF',
                cursor: loading ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8,
                boxShadow: '0 4px 12px rgba(7, 47, 55, 0.25)',
              }}
            >
              {loading && !activeQuickLogin ? (
                <>
                  <span className="spinner" style={{ width: 18, height: 18, borderWidth: 2 }} />
                  Authenticating...
                </>
              ) : (
                'Sign In to Dashboard →'
              )}
            </button>
          </form>

          {/* Quick Demo Accounts Header */}
          <div style={{ marginTop: 28, marginBottom: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ flex: 1, height: 1, background: '#E2E8F0' }} />
              <span
                style={{
                  fontSize: 11,
                  color: '#64748B',
                  fontWeight: 700,
                  letterSpacing: 0.8,
                  textTransform: 'uppercase',
                }}
              >
                ⚡ 1-Click Demo Evaluation Accounts
              </span>
              <div style={{ flex: 1, height: 1, background: '#E2E8F0' }} />
            </div>
            <p
              style={{
                textAlign: 'center',
                fontSize: 11,
                color: '#94A3B8',
                margin: '4px 0 0 0',
              }}
            >
              Click any role card to authenticate instantly and explore that role's view
            </p>
          </div>

          {/* 6 Demo Role Cards (2 columns x 3 rows) */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: 8,
            }}
          >
            {DEMO_CREDS.map((cred) => {
              const isSelected = activeQuickLogin === cred.email;
              return (
                <button
                  key={cred.email}
                  type="button"
                  onClick={() => handleQuickLogin(cred)}
                  disabled={loading}
                  style={{
                    background: isSelected ? `${cred.color}15` : '#F8FAFC',
                    border: `1.5px solid ${isSelected ? cred.color : '#E2E8F0'}`,
                    borderRadius: 8,
                    padding: '10px 12px',
                    cursor: loading ? 'wait' : 'pointer',
                    textAlign: 'left',
                    transition: 'all 0.15s ease',
                    position: 'relative',
                    boxShadow: isSelected ? '0 2px 8px rgba(0,0,0,0.06)' : 'none',
                  }}
                  onMouseEnter={(e) => {
                    if (!isSelected && !loading) {
                      e.currentTarget.style.borderColor = cred.color;
                      e.currentTarget.style.background = '#FFFFFF';
                      e.currentTarget.style.transform = 'translateY(-1px)';
                      e.currentTarget.style.boxShadow = '0 4px 10px rgba(0,0,0,0.05)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isSelected && !loading) {
                      e.currentTarget.style.borderColor = '#E2E8F0';
                      e.currentTarget.style.background = '#F8FAFC';
                      e.currentTarget.style.transform = 'none';
                      e.currentTarget.style.boxShadow = 'none';
                    }
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      marginBottom: 3,
                    }}
                  >
                    <span
                      style={{
                        fontSize: 12,
                        fontWeight: 700,
                        color: cred.color,
                      }}
                    >
                      {cred.label}
                    </span>
                    <span
                      style={{
                        fontSize: 9,
                        fontWeight: 700,
                        color: '#64748B',
                        background: '#E2E8F0',
                        padding: '1px 5px',
                        borderRadius: 4,
                      }}
                    >
                      {cred.targetView}
                    </span>
                  </div>
                  <div
                    style={{
                      fontSize: 11,
                      color: '#475569',
                      fontWeight: 500,
                      lineHeight: 1.3,
                    }}
                  >
                    {cred.desc}
                  </div>
                  <div
                    style={{
                      fontSize: 10,
                      color: '#94A3B8',
                      marginTop: 4,
                      fontFamily: 'monospace',
                    }}
                  >
                    {cred.email}
                  </div>

                  {isSelected && (
                    <div
                      style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        background: 'rgba(255,255,255,0.85)',
                        borderRadius: 7,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: 6,
                        color: cred.color,
                        fontWeight: 700,
                        fontSize: 11,
                      }}
                    >
                      <span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
                      Logging in...
                    </div>
                  )}
                </button>
              );
            })}
          </div>

          {/* Citizen Portal Direct Link */}
          <div
            style={{
              marginTop: 18,
              padding: '10px 14px',
              borderRadius: 8,
              background: '#F1F5F9',
              border: '1px solid #E2E8F0',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <span style={{ fontSize: 12, fontWeight: 700, color: '#334155' }}>
                Are you a Landowner / Citizen?
              </span>
              <div style={{ fontSize: 11, color: '#64748B' }}>
                Track your survey number without logging in
              </div>
            </div>
            <button
              type="button"
              onClick={() => navigate('/citizen')}
              style={{
                background: '#FFFFFF',
                border: '1px solid #CBD5E1',
                padding: '6px 12px',
                borderRadius: 6,
                fontSize: 11,
                fontWeight: 600,
                color: '#1B6CA8',
                cursor: 'pointer',
              }}
            >
              Citizen Portal ↗
            </button>
          </div>

          {/* Footer Metadata */}
          <p
            style={{
              marginTop: 20,
              textAlign: 'center',
              fontSize: 11,
              color: '#94A3B8',
              lineHeight: 1.5,
              margin: '20px 0 0 0',
            }}
          >
            Government of India — Ministry of Rural Development (MoRD)<br />
            Smart India Hackathon 2026 · Problem Statement SIH26016
          </p>
        </div>
      </div>
    </div>
  );
}
