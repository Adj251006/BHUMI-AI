import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  severity: 'critical' | 'high' | 'medium' | 'info';
  link_url?: string;
  action_label?: string;
  is_read: boolean;
  entity_type?: string;
  entity_id?: string;
  created_at?: string;
}

interface NotificationDropdownProps {
  isOpen: boolean;
  onClose: () => void;
  notifications: NotificationItem[];
  onMarkRead: (id: string) => void;
  onMarkAllRead: () => void;
}

function formatRelativeTime(dateStr?: string): string {
  if (!dateStr) return 'Just now';
  try {
    const d = new Date(dateStr);
    const now = new Date();
    const diffSec = Math.floor((now.getTime() - d.getTime()) / 1000);
    if (diffSec < 60) return 'Just now';
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin} min ago`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr} hr${diffHr > 1 ? 's' : ''} ago`;
    const diffDays = Math.floor(diffHr / 24);
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  } catch {
    return dateStr;
  }
}

export default function NotificationDropdown({
  isOpen,
  onClose,
  notifications,
  onMarkRead,
  onMarkAllRead,
}: NotificationDropdownProps) {
  const dropdownRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const unreadCount = notifications.filter(n => !n.is_read).length;

  const handleItemClick = (item: NotificationItem) => {
    if (!item.is_read) {
      onMarkRead(item.id);
    }
    onClose();

    if (item.link_url) {
      navigate(item.link_url);
    } else if (item.entity_type === 'project' || item.title.includes('RJ-HWY-024') || item.title.includes('Highway')) {
      navigate('/project/12345678-1234-5678-1234-567812345678');
    } else if (item.entity_type === 'compensation' || item.title.toLowerCase().includes('compensation')) {
      navigate('/compensation');
    } else if (item.entity_type === 'dispute' || item.title.toLowerCase().includes('dispute')) {
      navigate('/disputes');
    } else if (item.entity_type === 'workflow' || item.entity_type === 'field' || item.title.toLowerCase().includes('verification')) {
      navigate('/workflow');
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'critical':
        return { icon: '🔴', color: '#E74C3C', bg: '#FDECEA', label: 'CRITICAL' };
      case 'high':
        return { icon: '🟠', color: '#E67E22', bg: '#FEF3E2', label: 'HIGH' };
      case 'medium':
        return { icon: '🟡', color: '#F39C12', bg: '#FEFAEC', label: 'ATTENTION' };
      default:
        return { icon: 'ℹ️', color: '#1B6CA8', bg: '#EBF5FC', label: 'INFO' };
    }
  };

  return (
    <div
      ref={dropdownRef}
      style={{
        position: 'absolute',
        top: 'calc(100% + 10px)',
        right: 0,
        width: '380px',
        maxWidth: 'calc(100vw - 32px)',
        maxHeight: '560px',
        background: '#FFFFFF',
        borderRadius: 14,
        boxShadow: '0 12px 36px rgba(0, 0, 0, 0.16), 0 2px 8px rgba(0, 0, 0, 0.08)',
        border: '1px solid #D1DCE8',
        zIndex: 99999,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        animation: 'notifSlideDown 0.18s ease-out',
      }}
    >
      {/* HEADER */}
      <div
        style={{
          padding: '14px 18px',
          borderBottom: '1px solid #E2E8F0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: '#FAFCFD',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 16 }}>🔔</span>
          <span style={{ fontWeight: 700, fontSize: 14, color: '#1A2332' }}>Notifications</span>
          {unreadCount > 0 && (
            <span
              style={{
                background: '#E74C3C',
                color: '#FFFFFF',
                fontSize: 11,
                fontWeight: 700,
                padding: '1px 7px',
                borderRadius: 12,
              }}
            >
              {unreadCount} new
            </span>
          )}
        </div>
        {unreadCount > 0 && (
          <button
            type="button"
            onClick={onMarkAllRead}
            style={{
              background: 'none',
              border: 'none',
              color: '#1B6CA8',
              fontSize: 12,
              fontWeight: 600,
              cursor: 'pointer',
              padding: '4px 6px',
              borderRadius: 6,
              transition: 'background 0.15s',
            }}
            onMouseEnter={e => (e.currentTarget.style.textDecoration = 'underline')}
            onMouseLeave={e => (e.currentTarget.style.textDecoration = 'none')}
          >
            Mark all as read
          </button>
        )}
      </div>

      {/* NOTIFICATION LIST */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          maxHeight: '430px',
        }}
      >
        {notifications.length === 0 ? (
          <div style={{ padding: '36px 20px', textAlign: 'center', color: '#718096', fontSize: 13 }}>
            <div style={{ fontSize: 24, marginBottom: 8 }}>🎉</div>
            No notifications at this time. All systems running normally.
          </div>
        ) : (
          notifications.map((item) => {
            const sev = getSeverityBadge(item.severity);
            const isUnread = !item.is_read;

            return (
              <div
                key={item.id}
                onClick={() => handleItemClick(item)}
                style={{
                  padding: '14px 18px',
                  borderBottom: '1px solid #EDF2F7',
                  display: 'flex',
                  gap: 12,
                  alignItems: 'flex-start',
                  cursor: 'pointer',
                  background: isUnread ? 'rgba(27, 108, 168, 0.04)' : '#FFFFFF',
                  transition: 'background 0.15s ease',
                  position: 'relative',
                }}
                onMouseEnter={e => (e.currentTarget.style.background = isUnread ? 'rgba(27, 108, 168, 0.08)' : '#F7FAFC')}
                onMouseLeave={e => (e.currentTarget.style.background = isUnread ? 'rgba(27, 108, 168, 0.04)' : '#FFFFFF')}
              >
                {/* Unread indicator dot */}
                {isUnread && (
                  <div
                    style={{
                      position: 'absolute',
                      top: 18,
                      right: 14,
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      background: '#1B6CA8',
                      boxShadow: '0 0 0 2px #EBF5FC',
                    }}
                  />
                )}

                {/* Icon */}
                <div
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: 8,
                    background: sev.bg,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 16,
                    flexShrink: 0,
                    marginTop: 2,
                  }}
                >
                  {sev.icon}
                </div>

                {/* Content */}
                <div style={{ flex: 1, paddingRight: isUnread ? 16 : 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                    <span
                      style={{
                        fontSize: 9,
                        fontWeight: 700,
                        letterSpacing: 0.5,
                        color: sev.color,
                        background: sev.bg,
                        padding: '1px 5px',
                        borderRadius: 4,
                      }}
                    >
                      {sev.label}
                    </span>
                    <span style={{ fontSize: 11, color: '#A0AEC0' }}>
                      {formatRelativeTime(item.created_at)}
                    </span>
                  </div>

                  <div
                    style={{
                      fontSize: 13,
                      fontWeight: isUnread ? 700 : 600,
                      color: '#1A2332',
                      lineHeight: 1.35,
                      marginBottom: 4,
                    }}
                  >
                    {item.title}
                  </div>

                  <div
                    style={{
                      fontSize: 12,
                      color: '#4A5568',
                      lineHeight: 1.4,
                    }}
                  >
                    {item.message}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* FOOTER */}
      <div
        style={{
          padding: '10px 16px',
          borderTop: '1px solid #E2E8F0',
          background: '#FAFCFD',
          textAlign: 'center',
        }}
      >
        <button
          type="button"
          onClick={() => {
            onClose();
            navigate('/projects');
          }}
          style={{
            background: 'none',
            border: 'none',
            color: '#1B6CA8',
            fontSize: 12,
            fontWeight: 600,
            cursor: 'pointer',
            padding: '6px 12px',
            borderRadius: 6,
            width: '100%',
          }}
          onMouseEnter={e => (e.currentTarget.style.background = '#EBF5FC')}
          onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
        >
          View all projects & notifications →
        </button>
      </div>
    </div>
  );
}
