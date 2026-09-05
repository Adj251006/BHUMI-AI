import { useState, useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, GeoJSON, useMapEvents } from 'react-leaflet';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { LogOut, Map as MapIcon, Layers } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

function getAuthToken(): string | null {
  return localStorage.getItem('bhumi_token') || localStorage.getItem('sih_token');
}

function MapEventHandler({ setBbox }: { setBbox: (bbox: any) => void }) {
  const map = useMapEvents({
    moveend(e) {
      const bounds = e.target.getBounds();
      setBbox({
        min_lat: bounds.getSouth(),
        min_lon: bounds.getWest(),
        max_lat: bounds.getNorth(),
        max_lon: bounds.getEast(),
      });
    },
  });

  useEffect(() => {
    if (map) {
      const bounds = map.getBounds();
      setBbox({
        min_lat: bounds.getSouth(),
        min_lon: bounds.getWest(),
        max_lat: bounds.getNorth(),
        max_lon: bounds.getEast(),
      });
    }
  }, [map, setBbox]);

  return null;
}

export interface MapViewProps {
  projectId?: string;
  onParcelClick?: (parcelId: string) => void;
  embedded?: boolean;
  initialCenter?: [number, number];
  initialZoom?: number;
}

export default function MapView({
  projectId,
  onParcelClick,
  embedded = false,
  initialCenter,
  initialZoom = 13,
}: MapViewProps) {
  const [geoData, setGeoData] = useState<any>(null);
  const [bbox, setBbox] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const token = getAuthToken();
    if (!token && !embedded) {
      navigate('/login');
    }
  }, [navigate, embedded]);

  // Center coordinate determination (Jaipur for Rajasthan / Pune for MH / provided)
  const defaultCenter = useMemo<[number, number]>(() => {
    if (initialCenter) return initialCenter;
    if (projectId === '052acc2a-7902-43a9-a183-55cea297b8d8') return [18.5204, 73.8567]; // Pune
    return [26.9124, 75.7873]; // Jaipur / Rajasthan default
  }, [initialCenter, projectId]);

  // Fetch project-specific parcels or bbox parcels
  useEffect(() => {
    const token = getAuthToken();
    const headers = token ? { Authorization: `Bearer ${token}` } : {};

    if (projectId) {
      setLoading(true);
      axios
        .get(`${API_BASE}/api/parcels/project/${projectId}`, { headers })
        .then((res) => {
          if (res.data && res.data.features && res.data.features.length > 0) {
            setGeoData(res.data);
          } else if (bbox) {
            // fallback to bbox search
            return axios.get(`${API_BASE}/api/parcels/spatial`, {
              params: {
                min_lon: bbox.min_lon,
                min_lat: bbox.min_lat,
                max_lon: bbox.max_lon,
                max_lat: bbox.max_lat,
              },
              headers,
            }).then(spatialRes => setGeoData(spatialRes.data));
          }
        })
        .catch((err) => {
          console.error('Failed to fetch project spatial data:', err);
        })
        .finally(() => setLoading(false));
      return;
    }

    if (!bbox) return;

    setLoading(true);
    axios
      .get(`${API_BASE}/api/parcels/spatial`, {
        params: {
          min_lon: bbox.min_lon,
          min_lat: bbox.min_lat,
          max_lon: bbox.max_lon,
          max_lat: bbox.max_lat,
        },
        headers,
      })
      .then((response) => setGeoData(response.data))
      .catch((err) => console.error('Failed to fetch spatial data:', err))
      .finally(() => setLoading(false));
  }, [projectId, bbox]);

  const handleLogout = () => {
    localStorage.removeItem('bhumi_token');
    localStorage.removeItem('sih_token');
    navigate('/login');
  };

  const getParcelStyle = (feature: any) => {
    const status = feature?.properties?.possession_status?.toLowerCase() || '';
    let color = '#6B7280'; // GREY (not started)

    if (status === 'possessed' || status === 'acquired') {
      color = '#10B981'; // GREEN (acquired)
    } else if (status === 'joint_survey' || status === 'survey' || status === 'in_progress') {
      color = '#EAB308'; // YELLOW (in progress)
    } else if (status === 'awarded' || status === 'compensation_pending') {
      color = '#F97316'; // ORANGE (compensation pending)
    } else if (status === 'disputed' || status === 'high_risk') {
      color = '#EF4444'; // RED (disputed/high-risk)
    } else if (status === 'notified' || status === 'notification' || status === 'pre_acquisition') {
      color = '#3B82F6'; // BLUE (notification)
    }

    return {
      color,
      weight: 2,
      opacity: 0.9,
      fillColor: color,
      fillOpacity: 0.4,
    };
  };

  const onEachFeature = (feature: any, layer: any) => {
    if (feature.properties) {
      const p = feature.properties;
      const status = p.possession_status?.replace(/_/g, ' ') || 'Unknown';
      const parcelId = p.id;

      layer.bindPopup(`
        <div style="font-family: Inter, sans-serif; padding: 4px; min-width: 200px;">
          <h3 style="font-weight: 700; font-size: 15px; margin: 0 0 6px 0; color: #072F37;">
            Survey No: ${p.survey_number}
          </h3>
          <p style="font-size: 12px; color: #64748b; margin: 0 0 8px 0;">
            ${p.village || 'N/A'}, ${p.taluka || p.district || ''}
          </p>
          <div style="font-size: 12px; line-height: 1.6; border-top: 1px solid #e2e8f0; padding-top: 6px;">
            <div><strong>Area:</strong> ${p.area_hectares} Hectares</div>
            <div><strong>Type:</strong> <span style="text-transform: capitalize;">${(p.land_type || '').replace(/_/g, ' ')}</span></div>
            <div><strong>Status:</strong> <span style="font-weight: 600; text-transform: capitalize;">${status}</span></div>
          </div>
          <button id="inspect-parcel-${parcelId}" style="margin-top: 10px; width: 100%; padding: 6px 10px; background: #072F37; color: #fff; border: none; border-radius: 4px; font-size: 11px; font-weight: 600; cursor: pointer;">
            Inspect Full Parcel Details 🔍
          </button>
        </div>
      `);

      layer.on('popupopen', () => {
        const btn = document.getElementById(`inspect-parcel-${parcelId}`);
        if (btn) {
          btn.onclick = () => onParcelClick?.(parcelId);
        }
      });

      layer.on('click', () => {
        if (onParcelClick) {
          onParcelClick(parcelId);
        }
      });
    }
  };

  const mapContent = (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <MapContainer
        center={defaultCenter}
        zoom={initialZoom}
        style={{ width: '100%', height: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapEventHandler setBbox={setBbox} />
        {geoData && (
          <GeoJSON
            key={JSON.stringify(geoData)}
            data={geoData}
            onEachFeature={onEachFeature}
            style={getParcelStyle}
          />
        )}
      </MapContainer>

      {/* Map Legend (Phase 4 consistent colors) */}
      <div
        style={{
          position: 'absolute',
          bottom: 16,
          right: 16,
          background: 'rgba(255, 255, 255, 0.94)',
          backdropFilter: 'blur(8px)',
          borderRadius: 8,
          boxShadow: '0 4px 14px rgba(0, 0, 0, 0.12)',
          padding: '10px 14px',
          fontSize: 11,
          zIndex: 1000,
          border: '1px solid rgba(0,0,0,0.08)',
          pointerEvents: 'auto',
        }}
      >
        <div style={{ fontWeight: 700, marginBottom: 6, color: '#1e293b' }}>
          Acquisition Status
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '4px 12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 10, height: 10, borderRadius: 2, background: '#10B981', display: 'inline-block' }} />
            <span>Acquired</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 10, height: 10, borderRadius: 2, background: '#EAB308', display: 'inline-block' }} />
            <span>In Progress</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 10, height: 10, borderRadius: 2, background: '#F97316', display: 'inline-block' }} />
            <span>Compensation</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 10, height: 10, borderRadius: 2, background: '#EF4444', display: 'inline-block' }} />
            <span>Disputed</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 10, height: 10, borderRadius: 2, background: '#3B82F6', display: 'inline-block' }} />
            <span>Notified</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 10, height: 10, borderRadius: 2, background: '#6B7280', display: 'inline-block' }} />
            <span>Not Started</span>
          </div>
        </div>
      </div>
    </div>
  );

  if (embedded) {
    return <div style={{ width: '100%', height: '100%' }}>{mapContent}</div>;
  }

  return (
    <div style={{ height: 'calc(100vh - 64px)', display: 'flex', flexDirection: 'column', background: '#fff' }}>
      <header
        style={{
          background: '#fff',
          borderBottom: '1px solid #e2e8f0',
          padding: '12px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          zIndex: 10,
          position: 'relative',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ padding: 8, background: 'rgba(7, 47, 55, 0.08)', borderRadius: 8, color: '#072F37' }}>
            <MapIcon size={22} />
          </div>
          <div>
            <h1 style={{ fontWeight: 700, fontSize: 18, color: '#0f172a', margin: 0 }}>
              National GIS Land Parcel Intelligence
            </h1>
            <p style={{ fontSize: 12, color: '#64748b', margin: 0 }}>
              Multi-layered parcel boundaries & statutory acquisition status
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              fontSize: 12,
              color: '#475569',
              background: '#f8fafc',
              padding: '6px 12px',
              borderRadius: 20,
              border: '1px solid #e2e8f0',
            }}
          >
            <Layers size={15} />
            {loading ? 'Querying PostGIS...' : `${geoData?.features?.length || 0} parcels rendered`}
          </div>

          <button
            onClick={handleLogout}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              fontSize: 12,
              fontWeight: 500,
              color: '#64748b',
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              padding: '6px 12px',
              borderRadius: 6,
            }}
          >
            <LogOut size={15} />
            Sign Out
          </button>
        </div>
      </header>

      <main style={{ flex: 1, position: 'relative' }}>{mapContent}</main>
    </div>
  );
}
