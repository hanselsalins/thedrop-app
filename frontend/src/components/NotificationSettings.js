import { useState, useEffect } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { Bell, BellOff } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const TOGGLES = [
  { key: 'streak_reminders', label: 'Streak Reminders', desc: 'Get reminded at 6 PM if you haven\'t read today' },
  { key: 'milestone_alerts', label: 'Milestone Alerts', desc: 'Celebrate when you hit 7, 30, 50, 100 day streaks' },
  { key: 'daily_news_alerts', label: 'Daily News Alerts', desc: 'Get notified when fresh news drops (coming soon)' },
];

export const NotificationSettings = ({ isKids, permission, onRequestPermission }) => {
  const { token } = useTheme();
  const [prefs, setPrefs] = useState({ streak_reminders: true, milestone_alerts: true, daily_news_alerts: true });
  const [loading, setLoading] = useState(true);
  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  const textColor = isKids ? '#1A1A1A' : '#EDEDED';
  const cardBg = isKids ? '#FFFFFF' : '#121212';
  const accentColor = isKids ? '#3A86FF' : '#CCFF00';

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await axios.get(`${BACKEND_URL}/api/notifications/settings`, { headers });
        setPrefs(res.data);
      } catch (e) {}
      setLoading(false);
    };
    if (token) fetch();
  }, [token]);

  const toggle = async (key) => {
    const newVal = !prefs[key];
    setPrefs(prev => ({ ...prev, [key]: newVal }));
    try {
      await axios.put(`${BACKEND_URL}/api/notifications/settings`,
        { [key]: newVal }, { headers });
    } catch (e) {
      setPrefs(prev => ({ ...prev, [key]: !newVal }));
    }
  };

  return (
    <div
      data-testid="notification-settings"
      className="rounded-xl overflow-hidden"
      style={{
        background: cardBg,
        border: isKids ? 'none' : '1px solid rgba(255,255,255,0.06)',
        boxShadow: isKids ? '0 2px 12px rgba(0,0,0,0.05)' : 'none',
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 pb-2">
        <div className="flex items-center gap-2">
          <Bell size={16} style={{ color: accentColor }} />
          <p className="text-xs font-bold tracking-wider uppercase opacity-50"
            style={{ fontFamily: 'JetBrains Mono, monospace', color: textColor }}>
            NOTIFICATIONS
          </p>
        </div>
        {permission !== 'granted' && (
          <button
            data-testid="enable-notifications-btn"
            onClick={onRequestPermission}
            className="px-3 py-1.5 rounded-lg text-[10px] font-bold tracking-wider uppercase"
            style={{
              fontFamily: 'JetBrains Mono, monospace',
              background: accentColor,
              color: isKids ? '#fff' : '#050505',
            }}
          >
            Enable
          </button>
        )}
      </div>

      {/* Permission status */}
      {permission === 'denied' && (
        <div className="mx-4 mb-2 px-3 py-2 rounded-lg"
          style={{ background: 'rgba(255,42,109,0.08)', border: '1px solid rgba(255,42,109,0.15)' }}>
          <p className="text-xs" style={{ fontFamily: 'Outfit, sans-serif', color: '#FF2A6D' }}>
            Notifications blocked. Enable them in your browser settings.
          </p>
        </div>
      )}

      {permission === 'granted' && (
        <div className="mx-4 mb-2 px-3 py-1.5 rounded-lg"
          style={{ background: isKids ? 'rgba(58,134,255,0.06)' : 'rgba(204,255,0,0.04)' }}>
          <p className="text-xs opacity-60" style={{ fontFamily: 'Outfit, sans-serif', color: textColor }}>
            Notifications are enabled
          </p>
        </div>
      )}

      {/* Toggles */}
      <div className="px-4 pb-3 space-y-1">
        {TOGGLES.map((t) => (
          <button
            key={t.key}
            data-testid={`notif-toggle-${t.key}`}
            onClick={() => toggle(t.key)}
            disabled={loading || permission === 'denied'}
            className="w-full flex items-center justify-between py-3 text-left"
            style={{ opacity: permission === 'denied' ? 0.4 : 1 }}
          >
            <div className="flex-1 mr-3">
              <p className="text-sm font-medium"
                style={{ fontFamily: 'Outfit, sans-serif', color: textColor }}>
                {t.label}
              </p>
              <p className="text-xs opacity-40 mt-0.5"
                style={{ fontFamily: 'Outfit, sans-serif', color: textColor }}>
                {t.desc}
              </p>
            </div>
            <div
              className="w-11 h-6 rounded-full flex items-center px-0.5 shrink-0 transition-all duration-200"
              style={{
                background: prefs[t.key] ? accentColor : (isKids ? '#ddd' : 'rgba(255,255,255,0.1)'),
              }}
            >
              <div
                className="w-5 h-5 rounded-full transition-transform duration-200"
                style={{
                  background: '#fff',
                  transform: prefs[t.key] ? 'translateX(20px)' : 'translateX(0)',
                  boxShadow: '0 1px 4px rgba(0,0,0,0.2)',
                }}
              />
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};
