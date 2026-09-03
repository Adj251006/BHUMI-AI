import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, GeoJSON, useMapEvents } from 'react-leaflet';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { LogOut, Map as MapIcon, Layers } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

function MapEventHandler({ setBbox }: { setBbox: (bbox: any) => void }) {
  const map = useMapEvents({
    moveend(e) {
      const bounds = e.target.getBounds();
      setBbox({
        min_lat: bounds.getSouth(),
        min_lon: bounds.getWest(),
        max_lat: bounds.getNorth(),
        max_lon: bounds.getEast()
      });
    }
  });

  useEffect(() => {
    if (map) {
      const bounds = map.getBounds();
      setBbox({
        min_lat: bounds.getSouth(),
        min_lon: bounds.getWest(),
        max_lat: bounds.getNorth(),
        max_lon: bounds.getEast()
      });
    }
  }, [map, setBbox]);

  return null;
}

export default function MapView() {
  const [geoData, setGeoData] = useState<any>(null);
  const [bbox, setBbox] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('sih_token');
    if (!token) {
      navigate('/login');
    }
  }, [navigate]);

  useEffect(() => {
    if (!bbox) return;

    const fetchSpatialData = async () => {
      setLoading(true);
      try {
        const response = await axios.get(`${API_BASE}/api/parcels/spatial`, {
          params: {
            min_lon: bbox.min_lon,
            min_lat: bbox.min_lat,
            max_lon: bbox.max_lon,
            max_lat: bbox.max_lat
          }
        });
        setGeoData(response.data);
      } catch (err) {
        console.error('Failed to fetch spatial data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchSpatialData();
  }, [bbox]);

  const handleLogout = () => {
    localStorage.removeItem('sih_token');
    navigate('/login');
  };

  const onEachFeature = (feature: any, layer: any) => {
    if (feature.properties) {
      layer.bindPopup(`
        <div class="p-2 font-sans">
          <h3 class="font-bold text-lg mb-1">Survey No: ${feature.properties.survey_number}</h3>
          <p class="text-sm text-slate-600 mb-2">${feature.properties.village || 'N/A'}, ${feature.properties.taluka || 'N/A'}, ${feature.properties.district}</p>
          <div class="grid grid-cols-2 gap-2 text-sm mt-3 pt-3 border-t border-slate-200">
            <div class="text-slate-500">Area</div>
            <div class="font-medium text-right">${feature.properties.area_hectares} Ha</div>
            
            <div class="text-slate-500">Land Type</div>
            <div class="font-medium text-right capitalize">${feature.properties.land_type.replace('_', ' ')}</div>
            
            <div class="text-slate-500">Status</div>
            <div class="font-medium text-right">
              <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 capitalize">
                ${feature.properties.possession_status.replace(/_/g, ' ')}
              </span>
            </div>
          </div>
        </div>
      `);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-white">
      <header className="bg-white border-b border-slate-200 shadow-sm z-10 relative px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3 text-indigo-600">
          <div className="p-2 bg-indigo-50 rounded-lg">
            <MapIcon className="h-6 w-6" />
          </div>
          <div>
            <h1 className="font-bold text-xl text-slate-900 leading-tight">Land Parcel Explorer</h1>
            <p className="text-sm text-slate-500">Interactive GIS View</p>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm text-slate-600 bg-slate-50 px-3 py-1.5 rounded-full border border-slate-200">
            <Layers className="h-4 w-4" />
            {loading ? 'Updating...' : `${geoData?.features?.length || 0} parcels in view`}
          </div>
          
          <button 
            onClick={handleLogout}
            className="flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-red-600 transition-colors px-3 py-2 rounded-lg hover:bg-red-50"
          >
            <LogOut className="h-4 w-4" />
            Sign Out
          </button>
        </div>
      </header>
      
      <main className="flex-1 relative z-0">
        <MapContainer 
          center={[18.5204, 73.8567]} // Pune default 
          zoom={13} 
          className="h-full w-full"
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
              style={{
                color: '#4f46e5',
                weight: 2,
                opacity: 0.8,
                fillColor: '#6366f1',
                fillOpacity: 0.3
              }}
            />
          )}
        </MapContainer>
      </main>
    </div>
  );
}
