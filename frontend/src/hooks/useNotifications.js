import { useState, useEffect, useCallback } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export function useNotifications() {
  const { token, user } = useTheme();
  const [permission, setPermission] = useState('default');
  const [milestone, setMilestone] = useState(null);

  useEffect(() => {
    if ('Notification' in window) {
      setPermission(Notification.permission);
    }
  }, []);

  const requestPermission = useCallback(async () => {
    if (!('Notification' in window)) return 'unsupported';
    const result = await Notification.requestPermission();
    setPermission(result);

    if (result === 'granted' && token) {
      // Register a pseudo-token for web push tracking
      try {
        await axios.post(`${BACKEND_URL}/api/notifications/register-device`,
          { token: `web-${Date.now()}`, platform: 'web' },
          { headers: { Authorization: `Bearer ${token}` } });
      } catch (e) {}

      // Send timezone
      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
      try {
        await axios.post(`${BACKEND_URL}/api/notifications/update-timezone?tz=${encodeURIComponent(tz)}`,
          {}, { headers: { Authorization: `Bearer ${token}` } });
      } catch (e) {}
    }
    return result;
  }, [token]);

  const sendLocalNotification = useCallback((title, body, icon = '/favicon.ico') => {
    if (permission !== 'granted') return;
    try {
      new Notification(title, { body, icon, badge: icon, tag: 'the-drop' });
    } catch (e) {}
  }, [permission]);

  // Check for pending milestones
  const checkMilestone = useCallback(async () => {
    if (!token) return;
    try {
      const res = await axios.get(`${BACKEND_URL}/api/notifications/pending-milestone`,
        { headers: { Authorization: `Bearer ${token}` } });
      if (res.data) {
        setMilestone(res.data);
        // Also send as browser notification
        if (permission === 'granted') {
          sendLocalNotification('The Drop - Milestone!',
            `${res.data.emoji} ${res.data.message}`);
        }
      }
    } catch (e) {}
  }, [token, permission, sendLocalNotification]);

  const acknowledgeMilestone = useCallback(async (notificationId) => {
    if (!token || !notificationId) return;
    try {
      await axios.post(`${BACKEND_URL}/api/notifications/acknowledge/${notificationId}`,
        {}, { headers: { Authorization: `Bearer ${token}` } });
      setMilestone(null);
    } catch (e) {}
  }, [token]);

  return {
    permission,
    requestPermission,
    sendLocalNotification,
    milestone,
    checkMilestone,
    acknowledgeMilestone,
  };
}
