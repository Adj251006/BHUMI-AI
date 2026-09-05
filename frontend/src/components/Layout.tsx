import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../api/client';
import BhumiCopilot from './BhumiCopilot';
import NotificationDropdown, { type NotificationItem } from './NotificationDropdown';

interface NavItem {
  path: string;
  label: string;
  icon: string;
  badge?: number | string;
  badgeType?: 'error' | 'warning' | 'success';
  roles?: string[];
}

const FALLBACK_NOTIFICATIONS: NotificationItem[] = [
  {
    id: 'notif-1',
    title: 'Critical Project Risk',
    message: 'Delhi-Jaipur Highway Expansion (RJ-HWY-024) has 93.1% delay risk with 49 projected days overrun.',
    severity: 'critical',
    entity_type: 'project',
    is_read: false,
    created_at: new Date(Date.now() - 5 * 60000).toISOString(),
  },
  {
    id: 'notif-2',
    title: 'Compensation Review Required',
    message: '53 compensation disbursement cases pending verification in Jaipur district office.',
    severity: 'high',
    entity_type: 'compensation',
    is_read: false,
    created_at: new Date(Date.now() - 18 * 60000).toISOString(),
  },
  {
    id: 'notif-3',
    title: 'Field Verification Assigned',
    message: 'A priority field verification task requires review on 7 critical disputed parcels.',
    severity: 'high',
    entity_type: 'workflow',
    is_read: false,
    created_at: new Date(Date.now() - 32 * 60000).toISOString(),
  },
  {
    id: 'notif-4',
    title: 'R&R Resettlement Backlog',
    message: '31 project-affected families currently undergoing rehabilitation eligibility review.',
    severity: 'medium',
    entity_type: 'rr',
    is_read: false,
    created_at: new Date(Date.now() - 58 * 60000).toISOString(),
  },
  {
    id: 'notif-5',
    title: 'Dispute Hearing Update',
    message: 'Lok Adalat session designated for survey title claims in Rajasthan.',
    severity: 'info',
    entity_type: 'dispute',
    is_read: true,
    created_at: new Date(Date.now() - 120 * 60000).toISOString(),
  },
];

const NAV_ITEMS: NavItem[] = [
  { path: '/dashboard', label: 'Command Center', icon: '🏛️' },
  { path: '/projects', label: 'Projects', icon: '📋' },
  { path: '/analytics', label: 'Analytics', icon: '📊' },
  { path: '/compensation', label: 'Compensation', icon: '💰', badge: 52, badgeType: 'error' },
  { path: '/disputes', label: 'Disputes', icon: '⚖️', badge: 18, badgeType: 'warning' },
  { path: '/rr', label: 'R&R Management', icon: '🏡' },
  { path: '/documents', label: 'Documents', icon: '📄' },
  { path: '/workflow', label: 'Workflow', icon: '🔄' },
  { path: '/field', label: 'Field Ops', icon: '📍', roles: ['field_officer', 'district_authority'] },
  { path: '/audit', label: 'Audit Trail', icon: '🔒', roles: ['auditor', 'central_ministry', 'district_authority', 'state_govt'] },
  { path: '/citizen', label: 'Citizen Portal', icon: '👥' },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [showNotif, setShowNotif] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);

  useEffect(() => {
    api.getNotifications()
      .then((data: any) => {
        if (Array.isArray(data) && data.length > 0) {
          setNotifications(data);
        } else {
          setNotifications(FALLBACK_NOTIFICATIONS);
        }
      })
      .catch(() => setNotifications(FALLBACK_NOTIFICATIONS));
  }, []);

  const visibleItems = NAV_ITEMS.filter(item =>
    !item.roles || (user && item.roles.includes(user.role))
  );

  const initials = user?.full_name?.split(' ').map(w => w[0]).slice(0, 2).join('') || 'U';
  const roleLabelMap: Record<string, string> = {
    central_ministry: 'Central Ministry',
    state_govt: 'State Government',
    district_authority: 'District Authority',
    project_agency: 'Project Agency',
    field_officer: 'Field Officer',
    auditor: 'Auditor',
    citizen: 'Citizen',
  };

  const currentPage = visibleItems.find(i => location.pathname.startsWith(i.path));

  const handleMarkRead = (id: string) => {
    api.markNotifRead(id).catch(() => {});
    setNotifications(prev => prev.map(n => (n.id === id ? { ...n, is_read: true } : n)));
  };

  const handleMarkAllRead = () => {
    api.markAllNotifsRead().catch(() => {});
    setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <div className="app-layout">
      {/* SIDEBAR */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-logo">
            <div className="sidebar-logo-icon">🌱</div>
            <div className="sidebar-logo-text">
              <h1>BHUMI-AI</h1>
              <p>LAND ACQUISITION PLATFORM</p>
            </div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-label">Navigation</div>
          {visibleItems.map(item => (
            <button
              key={item.path}
              className={`nav-item ${location.pathname.startsWith(item.path) ? 'active' : ''}`}
              onClick={() => navigate(item.path)}
            >
              <span style={{ fontSize: 16, flexShrink: 0 }}>{item.icon}</span>
              <span>{item.label}</span>
              {item.badge && (
                <span className={`nav-item-badge${item.badgeType === 'warning' ? ' warning' : item.badgeType === 'success' ? ' success' : ''}`}>
                  {item.badge}
                </span>
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="user-card" onClick={logout} title="Click to logout">
            <div className="user-avatar">{initials}</div>
            <div className="user-info">
              <div className="user-name truncate">{user?.full_name}</div>
              <div className="user-role">{roleLabelMap[user?.role || ''] || user?.role}</div>
            </div>
            <span style={{ color: 'rgba(200,221,230,0.6)', fontSize: 12 }}>↗</span>
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT */}
      <div className="main-content">
        {/* TOP NAV */}
        <header className="top-nav">
          <div>
            <div className="topnav-title">
              {currentPage?.label || 'BHUMI-AI'}
            </div>
            {user?.state && (
              <div className="topnav-subtitle">
                {user.state}{user.district ? ` · ${user.district}` : ''}
              </div>
            )}
          </div>

          <div className="topnav-actions">
            <div style={{ position: 'relative' }}>
              <button
                className="btn-icon"
                onClick={() => setShowNotif(!showNotif)}
                title="Notifications"
                aria-label="Open notifications"
                style={{
                  background: showNotif ? '#EEF5F8' : 'transparent',
                  borderColor: showNotif ? '#1B6CA8' : 'var(--border)',
                }}
              >
                🔔
                {unreadCount > 0 && (
                  <span
                    style={{
                      position: 'absolute',
                      top: -2,
                      right: -2,
                      background: '#E74C3C',
                      color: 'white',
                      fontSize: 10,
                      fontWeight: 700,
                      minWidth: 18,
                      height: 18,
                      borderRadius: 9,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      padding: '0 4px',
                      border: '2px solid white',
                    }}
                  >
                    {unreadCount}
                  </span>
                )}
              </button>

              <NotificationDropdown
                isOpen={showNotif}
                onClose={() => setShowNotif(false)}
                notifications={notifications}
                onMarkRead={handleMarkRead}
                onMarkAllRead={handleMarkAllRead}
              />
            </div>
            <button className="btn-icon" onClick={() => navigate('/citizen')} title="Citizen Portal">🌐</button>
            <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'linear-gradient(135deg, var(--teal), var(--teal-dark))', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 700, fontSize: 13, cursor: 'pointer' }}>
              {initials}
            </div>
          </div>
        </header>

        {/* PAGE */}
        <main className="page-content fade-in">
          {children}
        </main>
      </div>

      {/* BHUMI COPILOT ASSISTANT */}
      <BhumiCopilot projectId={location.pathname.match(/\/project\/([a-zA-Z0-9-]+)/)?.[1]} />
    </div>
  );
}
