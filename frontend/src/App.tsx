import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Layout from './components/Layout';
import Login from './components/Login';
import Dashboard from './pages/Dashboard';
import StateDashboard from './pages/StateDashboard';
import Projects from './pages/Projects';
import ProjectDetail from './pages/ProjectDetail';
import Compensation from './pages/Compensation';
import Disputes from './pages/Disputes';
import Documents from './pages/Documents';
import Workflow from './pages/Workflow';
import Simulator from './pages/Simulator';
import Analytics from './pages/Analytics';
import FieldDashboard from './pages/FieldDashboard';
import CitizenPortal from './pages/CitizenPortal';
import AuditLog from './pages/AuditLog';
import RRManagement from './pages/RRManagement';
import LandBank from './pages/LandBank';
import MapView from './components/Map';

function ProtectedRoute({ children, allowedRoles }: { children: React.ReactNode; allowedRoles?: string[] }) {
  const { user, token, isLoading } = useAuth();
  if (isLoading) return <div className="loading-overlay"><div className="spinner" style={{ width: 36, height: 36 }} /></div>;
  if (!token) return <Navigate to="/login" replace />;
  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }
  return <Layout>{children}</Layout>;
}

function AppRoutes() {
  const { token } = useAuth();
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/citizen" element={<CitizenPortal />} />

      <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/dashboard/state/:stateName" element={<ProtectedRoute><StateDashboard /></ProtectedRoute>} />
      <Route path="/state/:stateName" element={<ProtectedRoute><StateDashboard /></ProtectedRoute>} />
      <Route path="/projects" element={<ProtectedRoute><Projects /></ProtectedRoute>} />
      <Route path="/project/:id" element={<ProtectedRoute><ProjectDetail /></ProtectedRoute>} />
      <Route path="/compensation" element={<ProtectedRoute><Compensation /></ProtectedRoute>} />
      <Route path="/disputes" element={<ProtectedRoute><Disputes /></ProtectedRoute>} />
      <Route path="/rr" element={<ProtectedRoute><RRManagement /></ProtectedRoute>} />
      <Route path="/land-bank" element={<ProtectedRoute><LandBank /></ProtectedRoute>} />
      <Route path="/documents" element={<ProtectedRoute><Documents /></ProtectedRoute>} />
      <Route path="/workflow" element={<ProtectedRoute><Workflow /></ProtectedRoute>} />
      <Route path="/simulator" element={<ProtectedRoute><Simulator /></ProtectedRoute>} />
      <Route path="/analytics" element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
      <Route path="/field" element={<ProtectedRoute allowedRoles={['field_officer', 'district_authority', 'central_ministry']}><FieldDashboard /></ProtectedRoute>} />
      <Route path="/audit" element={<ProtectedRoute allowedRoles={['auditor', 'central_ministry', 'district_authority', 'state_govt']}><AuditLog /></ProtectedRoute>} />
      <Route path="/map" element={<ProtectedRoute><MapView /></ProtectedRoute>} />

      <Route path="/" element={<Navigate to={token ? "/dashboard" : "/login"} replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Router>
  );
}
