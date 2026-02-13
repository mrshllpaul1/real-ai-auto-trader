import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Bell, Check, CheckCheck, Volume2, Phone } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';

const NotificationCenter = () => {
  const [notifications, setNotifications] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const dropdownRef = useRef(null);

  const fetchNotifications = useCallback(async () => {
    try {
      const res = await api.get('/notifications/?limit=20');
      const notifs = res.data.notifications || [];
      setNotifications(notifs);
      setUnreadCount(notifs.filter(n => !n.read).length);
    } catch (e) {
      console.error('Failed to fetch notifications:', e);
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const markAsRead = async (notificationId) => {
    try {
      await api.post('/notifications/mark-read/' + notificationId);
      setNotifications(prev =>
        prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (e) {
      console.error('Failed to mark notification as read:', e);
    }
  };

  const markAllRead = async () => {
    try {
      await api.post('/notifications/mark-all-read');
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      setUnreadCount(0);
    } catch (e) {
      console.error('Failed to mark all as read:', e);
    }
  };

  const getNotificationIcon = (notif) => {
    const type = notif.data?.type;
    if (type === 'trade_completed') {
      return notif.data?.profit_pct >= 0 ? '🟢' : '🔴';
    }
    if (type === 'high_alert') return '🚨';
    return '🔔';
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return diffMins + 'm ago';
    if (diffMins < 1440) return Math.floor(diffMins / 60) + 'h ago';
    return date.toLocaleDateString();
  };

  return (
    <div className="relative" ref={dropdownRef} data-testid="notification-center">
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setIsOpen(!isOpen)}
        className="relative text-[#A1A1AA] hover:text-white"
        data-testid="notification-bell"
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <Badge className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 bg-[#FF0055] text-white text-xs">
            {unreadCount > 9 ? '9+' : unreadCount}
          </Badge>
        )}
      </Button>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            className="absolute top-full left-0 mt-2 w-80 max-w-[calc(100vw-1rem)] bg-[#0A0A0A] border border-[#1F1F1F] rounded-lg shadow-xl z-[100] overflow-hidden"
            style={{ minWidth: '300px' }}
          >
            <div className="flex items-center justify-between p-3 border-b border-[#1F1F1F]">
              <span className="font-bold text-white">Notifications</span>
              {unreadCount > 0 && (
                <Button variant="ghost" size="sm" onClick={markAllRead} className="text-xs text-[#00FF94]">
                  <CheckCheck size={14} className="mr-1" />Mark all read
                </Button>
              )}
            </div>
            <div className="max-h-96 overflow-y-auto">
              {notifications.length > 0 ? notifications.map((notif) => (
                <div
                  key={notif.id}
                  className={`p-3 border-b border-[#1F1F1F] hover:bg-[#121212] cursor-pointer ${!notif.read ? 'bg-[#00FF94]/5' : ''}`}
                  onClick={() => markAsRead(notif.id)}
                >
                  <div className="flex items-start gap-2">
                    <span className="text-lg">{getNotificationIcon(notif)}</span>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-white text-sm truncate">{notif.title}</p>
                      <p className="text-xs text-[#A1A1AA] mt-1 line-clamp-2">{notif.body}</p>
                      <p className="text-xs text-[#666] mt-1">{formatTime(notif.timestamp)}</p>
                    </div>
                    {!notif.read && <div className="w-2 h-2 rounded-full bg-[#00FF94] mt-2" />}
                  </div>
                </div>
              )) : (
                <div className="p-6 text-center">
                  <Bell size={32} className="mx-auto mb-2 text-[#333]" />
                  <p className="text-[#A1A1AA] text-sm">No notifications yet</p>
                </div>
              )}
            </div>
            <div className="p-2 border-t border-[#1F1F1F] flex items-center justify-center gap-4 text-xs text-[#666]">
              <div className="flex items-center gap-1"><Volume2 size={12} /><span>Push: ON</span></div>
              <div className="flex items-center gap-1"><Phone size={12} /><span>SMS: Configured</span></div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default NotificationCenter;
