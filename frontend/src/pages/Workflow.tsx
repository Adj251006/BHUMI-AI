import React, { useEffect, useState } from 'react';
import { api } from '../api/client';

export default function Workflow() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState('');

  // Statutory State Machine State
  const [workflowRules, setWorkflowRules] = useState<any>(null);
  const [parcels, setParcels] = useState<any[]>([]);
  const [selectedParcelId, setSelectedParcelId] = useState<string>('');
  const [transitionTarget, setTransitionTarget] = useState<string>('');
  const [transitionRemarks, setTransitionRemarks] = useState<string>('');
  const [transitioning, setTransitioning] = useState(false);
  const [transitionFeedback, setTransitionFeedback] = useState<{ success: boolean; message: string } | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const [tData, rData, pData] = await Promise.all([
        api.getTasks(),
        api.getWorkflowRules().catch(() => null),
        api.getParcels().catch(() => []),
      ]);
      setTasks(tData || []);
      setWorkflowRules(rData);
      const parcelList = pData || [];
      setParcels(parcelList);
      if (parcelList.length > 0 && !selectedParcelId) {
        setSelectedParcelId(parcelList[0].id);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const selectedParcel = parcels.find(p => p.id === selectedParcelId) || parcels[0];

  // Derive current workflow stage from parcel possession_status
  const getCurrentStage = (parcel: any) => {
    if (!parcel) return 'section_11_notification';
    const s = parcel.possession_status;
    if (s === 'not_acquired') return 'section_11_notification';
    if (s === 'notice_issued') return 'hearing_objections';
    if (s === 'awarded') return 'enquiry_and_award';
    if (s === 'possessed') return 'possession';
    return 'section_11_notification';
  };

  const currentStage = getCurrentStage(selectedParcel);
  const currentRule = workflowRules?.statutory_stages?.[currentStage];
  const allowedNextStages: string[] = currentRule?.allowed_transitions || [];

  const handleExecuteTransition = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedParcelId || !transitionTarget) return;
    setTransitioning(true);
    setTransitionFeedback(null);
    try {
      const res = await api.transitionWorkflowStage(selectedParcelId, transitionTarget, transitionRemarks);
      setTransitionFeedback({
        success: true,
        message: `Statutory transition approved: ${res.previous_stage} ➔ ${res.new_stage}. Registered in audit log.`,
      });
      // Refresh parcels
      const updatedParcels = await api.getParcels();
      setParcels(updatedParcels || []);
      setTransitionRemarks('');
    } catch (err: any) {
      setTransitionFeedback({
        success: false,
        message: err.message || 'Transition rejected by RFCTLARR statutory rules engine.',
      });
    } finally {
      setTransitioning(false);
    }
  };

  const updateStatus = async (id: string, status: string) => {
    setUpdating(id);
    try {
      await api.updateTaskStatus(id, status);
      const t = await api.getTasks();
      setTasks(t || []);
    } catch (e) {
      console.error(e);
    } finally {
      setUpdating(null);
    }
  };

  const filtered = statusFilter ? tasks.filter(t => t.status === statusFilter) : tasks;
  const overdue = tasks.filter(t => t.due_date && new Date(t.due_date) < new Date() && t.status !== 'completed');

  const statutoryPipeline = [
    { key: 'proposal', name: '1. Proposal' },
    { key: 'sia_notification', name: '2. Sec 4 (SIA)' },
    { key: 'sia_report', name: '3. Sec 7 (Report)' },
    { key: 'section_11_notification', name: '4. Sec 11 (Prelim)' },
    { key: 'hearing_objections', name: '5. Sec 15 (Hearings)' },
    { key: 'rr_scheme', name: '6. Sec 16 (R&R)' },
    { key: 'section_19_declaration', name: '7. Sec 19 (Decl)' },
    { key: 'notice_interested_persons', name: '8. Sec 21 (Notice)' },
    { key: 'enquiry_and_award', name: '9. Sec 23 (Award)' },
    { key: 'compensation_disbursement', name: '10. Compensation' },
    { key: 'possession', name: '11. Sec 38 (Possess)' },
    { key: 'handover', name: '12. Handover' },
  ];

  if (loading) return <div className="loading-overlay"><div className="spinner" style={{ width: 36, height: 36 }} /></div>;

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* HEADER */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <span style={{ fontSize: 22 }}>⚖️</span>
            <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1.5, textTransform: 'uppercase', color: '#1B6CA8' }}>
              RFCTLARR ACT 2013 STATUTORY STATE MACHINE
            </span>
          </div>
          <h1 style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
            Statutory Workflow & Stage Transitions
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, margin: '4px 0 0' }}>
            Legally-enforced state transitions with strict statutory SLAs, prerequisite checking, and anti-circumvention rules.
          </p>
        </div>
      </div>

      {/* STATUTORY 12-STAGE PIPELINE STRIP */}
      <div className="card" style={{ padding: '20px 24px' }}>
        <div style={{ fontSize: 13, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 14 }}>
          Statutory 12-Stage Acquisition Pipeline (Section 4 to Section 40)
        </div>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
            gap: 8,
          }}
        >
          {statutoryPipeline.map((stage, idx) => {
            const isSelectedStage = stage.key === currentStage;
            const stageIndex = statutoryPipeline.findIndex(s => s.key === currentStage);
            const isCompleted = idx < stageIndex;

            return (
              <div
                key={stage.key}
                style={{
                  background: isSelectedStage ? '#1B6CA8' : isCompleted ? '#ECFDF5' : '#F8FAFC',
                  color: isSelectedStage ? '#FFFFFF' : isCompleted ? '#065F46' : '#64748B',
                  border: isSelectedStage ? '1.5px solid #1B6CA8' : isCompleted ? '1.5px solid #A7F3D0' : '1px solid #E2E8F0',
                  borderRadius: 10,
                  padding: '10px 8px',
                  textAlign: 'center',
                  fontSize: 11,
                  fontWeight: isSelectedStage || isCompleted ? 700 : 500,
                  boxShadow: isSelectedStage ? '0 4px 12px rgba(27, 108, 168, 0.25)' : 'none',
                }}
              >
                <div>{isCompleted ? '✓' : isSelectedStage ? '●' : '○'}</div>
                <div style={{ marginTop: 4, lineHeight: 1.2 }}>{stage.name}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* INTERACTIVE STAGE TRANSITION CONTROLLER */}
      <div
        className="card"
        style={{
          padding: '24px 28px',
          background: 'linear-gradient(135deg, #FFFFFF, #F8FAFC)',
          border: '1.5px solid #CBD5E1',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h3 style={{ fontSize: 17, fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
              ⚡ Statutory State Transition Engine
            </h3>
            <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: '2px 0 0' }}>
              Enforce RFCTLARR Act legal prerequisites before advancing parcel acquisition state.
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <label style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)' }}>Select Target Parcel:</label>
            <select
              className="form-input"
              value={selectedParcelId}
              onChange={e => {
                setSelectedParcelId(e.target.value);
                setTransitionTarget('');
                setTransitionFeedback(null);
              }}
              style={{ width: 220, fontSize: 13, fontWeight: 600 }}
            >
              {parcels.map(p => (
                <option key={p.id} value={p.id}>
                  Survey {p.survey_number} ({p.village})
                </option>
              ))}
            </select>
          </div>
        </div>

        {selectedParcel && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Current Stage Status Banner */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: 14,
                background: '#FFFFFF',
                padding: '16px 20px',
                borderRadius: 12,
                border: '1px solid #E2E8F0',
              }}
            >
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>CURRENT STATUTORY STAGE</div>
                <div style={{ fontSize: 15, fontWeight: 800, color: '#1B6CA8', marginTop: 2 }}>
                  {currentRule?.title || currentStage.replace(/_/g, ' ').toUpperCase()}
                </div>
              </div>
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>STATUTORY SLA LIMIT</div>
                <div style={{ fontSize: 15, fontWeight: 800, color: '#D97706', marginTop: 2 }}>
                  ⏱️ {currentRule?.max_statutory_days ? `${currentRule.max_statutory_days} Days Max` : 'Not Applicable'}
                </div>
              </div>
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>MANDATORY PREREQUISITE</div>
                <div style={{ fontSize: 12, fontWeight: 600, color: '#334155', marginTop: 2 }}>
                  {currentRule?.prerequisites?.[0] || 'Valid Section 11 Preliminary Gazette Notification'}
                </div>
              </div>
            </div>

            {/* Transition Form */}
            <form onSubmit={handleExecuteTransition} style={{ display: 'flex', gap: 12, alignItems: 'flex-end', flexWrap: 'wrap' }}>
              <div style={{ flex: 1, minWidth: 240 }}>
                <label style={{ fontSize: 12, fontWeight: 700, display: 'block', marginBottom: 6 }}>
                  Target Next Stage (Legally Permitted)
                </label>
                <select
                  className="form-input"
                  value={transitionTarget}
                  onChange={e => setTransitionTarget(e.target.value)}
                  required
                >
                  <option value="">-- Choose Legally Permitted Stage --</option>
                  {allowedNextStages.map(stg => (
                    <option key={stg} value={stg}>
                      ➔ {stg.replace(/_/g, ' ').toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ flex: 2, minWidth: 280 }}>
                <label style={{ fontSize: 12, fontWeight: 700, display: 'block', marginBottom: 6 }}>
                  Statutory Order / Gazetted Remarks
                </label>
                <input
                  className="form-input"
                  value={transitionRemarks}
                  onChange={e => setTransitionRemarks(e.target.value)}
                  placeholder="e.g. Gazette Order No. 491/2026 issued after completion of 60-day objections."
                  required
                />
              </div>

              <button
                id="advance-stage-btn"
                type="submit"
                className="btn btn-primary"
                disabled={transitioning || !transitionTarget}
                style={{ padding: '10px 20px', fontWeight: 700, borderRadius: 10 }}
              >
                {transitioning ? 'Validating...' : 'Advance Stage ➔'}
              </button>
            </form>

            {transitionFeedback && (
              <div
                style={{
                  padding: '12px 16px',
                  borderRadius: 10,
                  fontSize: 13,
                  fontWeight: 600,
                  background: transitionFeedback.success ? '#ECFDF5' : '#FEF2F2',
                  color: transitionFeedback.success ? '#065F46' : '#991B1B',
                  border: transitionFeedback.success ? '1px solid #A7F3D0' : '1px solid #FCA5A5',
                }}
              >
                {transitionFeedback.success ? '✅ ' : '⛔ '}
                {transitionFeedback.message}
              </div>
            )}
          </div>
        )}
      </div>

      {/* STATS */}
      <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(5, 1fr)' }}>
        {[
          { label: 'Total Tasks', value: tasks.length, color: 'teal' },
          { label: 'In Progress', value: tasks.filter(t => t.status === 'in_progress').length, color: 'teal' },
          { label: 'Pending Review', value: tasks.filter(t => t.status === 'pending_review').length, color: 'saffron' },
          { label: 'Overdue (SLA Risk)', value: overdue.length, color: 'red' },
          { label: 'Completed', value: tasks.filter(t => t.status === 'completed').length, color: 'green' },
        ].map(s => (
          <div key={s.label} className={`kpi-card ${s.color}`} style={{ padding: 16 }}>
            <div className="kpi-value" style={{ fontSize: 28 }}>{s.value}</div>
            <div className="kpi-label">{s.label}</div>
          </div>
        ))}
      </div>

      {overdue.length > 0 && (
        <div className="alert critical">
          <span>🔴</span>
          <div>
            <strong>{overdue.length} overdue task{overdue.length > 1 ? 's' : ''}</strong> violate statutory RFCTLARR limitation periods. Priority escalation active.
          </div>
        </div>
      )}

      {/* Filter tabs */}
      <div className="tabs" style={{ maxWidth: 600 }}>
        {['', 'in_progress', 'pending_review', 'overdue', 'completed'].map(s => (
          <button key={s} className={`tab ${statusFilter === s ? 'active' : ''}`} onClick={() => setStatusFilter(s)}>
            {s === '' ? 'All Tasks' : s.replace(/_/g, ' ').toUpperCase()}
          </button>
        ))}
      </div>

      {/* TASKS TABLE */}
      <div className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Statutory Task</th>
              <th>Stage</th>
              <th>Priority</th>
              <th>Status</th>
              <th>Assigned Officer</th>
              <th>Due Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((t: any) => {
              const isOverdue = t.due_date && new Date(t.due_date) < new Date() && t.status !== 'completed';
              return (
                <tr key={t.id} style={{ background: isOverdue ? 'var(--red-bg)' : 'transparent' }}>
                  <td>
                    <div style={{ fontWeight: 600, fontSize: 13, maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {t.title}
                    </div>
                    {t.is_escalated && <span className="badge high" style={{ marginTop: 4 }}>🔴 Escalated</span>}
                  </td>
                  <td><span className="badge info">{t.stage}</span></td>
                  <td><span className={`badge ${t.priority}`}>{t.priority}</span></td>
                  <td><span className={`badge ${t.status}`}>{t.status.replace(/_/g, ' ')}</span></td>
                  <td style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{t.assigned_to ? '👤 CALA Officer' : '—'}</td>
                  <td style={{ fontSize: 12, color: isOverdue ? 'var(--red)' : 'var(--text-secondary)', fontWeight: isOverdue ? 700 : 400 }}>
                    {t.due_date ? new Date(t.due_date).toLocaleDateString('en-IN') : '—'}
                    {isOverdue && <div style={{ fontSize: 10 }}>⚠️ OVERDUE</div>}
                  </td>
                  <td>
                    {t.status === 'in_progress' && (
                      <button className="btn btn-secondary btn-sm" disabled={updating === t.id} onClick={() => updateStatus(t.id, 'pending_review')}>
                        {updating === t.id ? '...' : 'Submit'}
                      </button>
                    )}
                    {t.status === 'pending_review' && (
                      <div style={{ display: 'flex', gap: 4 }}>
                        <button className="btn btn-primary btn-sm" disabled={updating === t.id} onClick={() => updateStatus(t.id, 'approved')}>Approve</button>
                        <button className="btn btn-ghost btn-sm" onClick={() => updateStatus(t.id, 'rejected')}>Reject</button>
                      </div>
                    )}
                    {t.status === 'approved' && <span style={{ color: 'var(--green)', fontWeight: 600, fontSize: 12 }}>✓ Approved</span>}
                    {isOverdue && t.status !== 'completed' && (
                      <button className="btn btn-danger btn-sm" onClick={() => updateStatus(t.id, 'escalated')}>Escalate</button>
                    )}
                  </td>
                </tr>
              );
            })}
            {filtered.length === 0 && (
              <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 32 }}>No tasks found</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
