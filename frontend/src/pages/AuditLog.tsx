import { useEffect, useState } from 'react';
import { api } from '../api/client';

export default function AuditLog() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState<any>(null);

  const load = () => {
    setLoading(true);
    api.getAuditLogs()
      .then(setLogs)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const handleVerifyChain = async () => {
    setVerifying(true);
    try {
      const res = await api.verifyAuditTrail();
      setVerificationResult(res);
    } catch (err: any) {
      alert(err.message || 'Audit trail verification failed');
    } finally {
      setVerifying(false);
    }
  };

  if (loading) return <div className="loading-overlay"><div className="spinner" style={{ width: 36, height: 36 }} /></div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* HEADER */}
      <div
        style={{
          background: 'linear-gradient(135deg, #1E293B, #334155)',
          color: 'white',
          padding: '24px 28px',
          borderRadius: 16,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 16,
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <span style={{ fontSize: 22 }}>⛓️</span>
            <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1.5, textTransform: 'uppercase', color: '#38BDF8' }}>
              NATIONAL AUDIT ENGINE · SHA-256 HASH-CHAINED LOG
            </span>
          </div>
          <h1 style={{ fontSize: 22, fontWeight: 800, margin: 0 }}>
            Comptroller & Auditor General (CAG) Immutable Audit Trail
          </h1>
          <p style={{ color: '#94A3B8', fontSize: 13, margin: '4px 0 0', maxWidth: 640 }}>
            Cryptographically linked tamper-evident audit ledger tracking every RFCTLARR transaction, stage transition, CALA award, and PFMS disbursement.
          </p>
        </div>

        <div style={{ display: 'flex', gap: 10 }}>
          <button
            type="button"
            id="verify-chain-btn"
            className="btn btn-primary"
            onClick={handleVerifyChain}
            disabled={verifying}
            style={{
              background: '#0284C7',
              borderColor: '#0284C7',
              padding: '10px 18px',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              borderRadius: 10,
            }}
          >
            {verifying ? '⛓️ Validating Chain...' : '🛡️ Cryptographically Verify Hash Chain'}
          </button>
        </div>
      </div>

      {/* VERIFICATION BANNER */}
      {verificationResult && (
        <div
          style={{
            padding: '16px 20px',
            borderRadius: 12,
            background: verificationResult.is_valid ? '#F0FDF4' : '#FEF2F2',
            border: verificationResult.is_valid ? '1.5px solid #86EFAC' : '1.5px solid #FCA5A5',
            color: verificationResult.is_valid ? '#14532D' : '#7F1D1D',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: 12,
          }}
        >
          <div>
            <div style={{ fontSize: 14, fontWeight: 800 }}>
              {verificationResult.is_valid
                ? '✅ Cryptographic Integrity Confirmed: Blockchain Hash Chain Valid'
                : '❌ Tampering Detected in Audit Log Chain!'}
            </div>
            <div style={{ fontSize: 12, marginTop: 4, color: verificationResult.is_valid ? '#166534' : '#991B1B' }}>
              {verificationResult.message} · Total Verified Entries: <strong>{verificationResult.total_entries}</strong>
              {verificationResult.genesis_hash && (
                <span> · Genesis: <code style={{ fontFamily: 'monospace' }}>{verificationResult.genesis_hash.slice(0, 12)}...</code></span>
              )}
            </div>
          </div>
          <button
            type="button"
            onClick={() => setVerificationResult(null)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 18 }}
          >
            ✕
          </button>
        </div>
      )}

      {/* LOGS TABLE */}
      <div className="card">
        <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 className="card-title">📜 Immutable Chain of Custody ({logs.length} Blocks)</h3>
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>SHA-256 Sequential Linkage</span>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Timestamp (UTC)</th>
                <th>Actor / Role</th>
                <th>Action</th>
                <th>Entity Target</th>
                <th>Prev Block Hash</th>
                <th>Entry Hash</th>
              </tr>
            </thead>
            <tbody>
              {logs.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 32 }}>
                    No audit logs recorded yet.
                  </td>
                </tr>
              ) : (
                logs.map(l => (
                  <tr key={l.id}>
                    <td style={{ fontSize: 12, whiteSpace: 'nowrap' }}>
                      {l.timestamp ? new Date(l.timestamp).toLocaleString('en-IN') : 'N/A'}
                    </td>
                    <td>
                      <div style={{ fontWeight: 700, fontSize: 13 }}>{l.user_email || 'System Daemon'}</div>
                      <span className="badge badge-info" style={{ fontSize: 10 }}>{l.user_role || 'ADMIN'}</span>
                    </td>
                    <td>
                      <span className="badge badge-success" style={{ textTransform: 'uppercase', fontSize: 11 }}>
                        {l.action}
                      </span>
                    </td>
                    <td>
                      <div style={{ fontSize: 12, fontWeight: 600 }}>{l.entity_type}</div>
                      <div style={{ fontSize: 10, fontFamily: 'monospace', color: 'var(--text-muted)' }}>
                        {l.entity_id?.slice(0, 10)}...
                      </div>
                    </td>
                    <td>
                      <code
                        style={{
                          fontSize: 11,
                          background: '#F1F5F9',
                          padding: '2px 6px',
                          borderRadius: 4,
                          color: '#475569',
                        }}
                        title={l.prev_hash}
                      >
                        {l.prev_hash ? l.prev_hash.slice(0, 10) + '...' : 'GENESIS'}
                      </code>
                    </td>
                    <td>
                      <code
                        style={{
                          fontSize: 11,
                          background: '#EFF6FF',
                          padding: '2px 6px',
                          borderRadius: 4,
                          color: '#1D4ED8',
                          fontWeight: 700,
                        }}
                        title={l.entry_hash}
                      >
                        {l.entry_hash ? l.entry_hash.slice(0, 10) + '...' : 'PENDING'}
                      </code>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
