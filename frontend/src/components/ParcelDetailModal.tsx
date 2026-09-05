import { useEffect, useState } from 'react';
import { api } from '../api/client';

interface Props {
  parcelId: string | null;
  onClose: () => void;
}

export default function ParcelDetailModal({ parcelId, onClose }: Props) {
  const [parcel, setParcel] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!parcelId) return;
    setLoading(true);
    api.getParcel(parcelId)
      .then(setParcel)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [parcelId]);

  if (!parcelId) return null;

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,0.5)', zIndex: 1000,
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20
    }}>
      <div style={{
        background: 'white', borderRadius: 16, width: '100%', maxWidth: 640,
        maxHeight: '90vh', overflowY: 'auto', padding: 24, boxShadow: 'var(--shadow-xl)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <h2 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>
            🗺️ Parcel Details: {parcel?.survey_number || parcelId}
          </h2>
          <button className="btn btn-ghost btn-sm" onClick={onClose}>✕</button>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: 40 }}><div className="spinner" /></div>
        ) : parcel ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, background: 'var(--bg-card)', padding: 16, borderRadius: 12 }}>
              <div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Survey Number</div>
                <div style={{ fontWeight: 600 }}>{parcel.survey_number}</div>
              </div>
              <div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Land Type</div>
                <div style={{ fontWeight: 600, textTransform: 'capitalize' }}>{parcel.land_type}</div>
              </div>
              <div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Area (Hectares)</div>
                <div style={{ fontWeight: 600 }}>{parcel.area_hectares} Ha</div>
              </div>
              <div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Ownership</div>
                <div style={{ fontWeight: 600, textTransform: 'capitalize' }}>{parcel.ownership_type}</div>
              </div>
              <div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>State / District</div>
                <div style={{ fontWeight: 600 }}>{parcel.state} · {parcel.district}</div>
              </div>
              <div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Possession Status</div>
                <span className={`badge ${parcel.possession_status === 'possessed' ? 'badge-success' : 'badge-warning'}`}>
                  {parcel.possession_status?.toUpperCase()}
                </span>
              </div>
            </div>

            <div style={{ padding: 16, border: '1px solid var(--border)', borderRadius: 12 }}>
              <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 8 }}>📍 Village / Location</div>
              <div style={{ fontSize: 13 }}>{parcel.village}, {parcel.taluka}, {parcel.district}, {parcel.state}</div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginTop: 12 }}>
              <button className="btn btn-outline" onClick={onClose}>Close</button>
            </div>
          </div>
        ) : (
          <div>Parcel data unavailable.</div>
        )}
      </div>
    </div>
  );
}
