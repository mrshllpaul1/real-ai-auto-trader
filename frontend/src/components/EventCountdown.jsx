import React, { useState, useEffect } from 'react';
import { Clock, Calendar, ChevronRight, Bell } from 'lucide-react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL || '';

const EventCountdown = ({ compact = false }) => {
  const [nextEvent, setNextEvent] = useState(null);
  const [countdown, setCountdown] = useState({ days: 0, hours: 0, minutes: 0, seconds: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchNextEvent();
  }, []);

  useEffect(() => {
    if (!nextEvent) return;

    const timer = setInterval(() => {
      const eventDate = new Date(nextEvent.date);
      const now = new Date();
      const diff = eventDate - now;

      if (diff <= 0) {
        setCountdown({ days: 0, hours: 0, minutes: 0, seconds: 0 });
        fetchNextEvent(); // Refresh to get next event
        return;
      }

      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((diff % (1000 * 60)) / 1000);

      setCountdown({ days, hours, minutes, seconds });
    }, 1000);

    return () => clearInterval(timer);
  }, [nextEvent]);

  const fetchNextEvent = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/event-countdown/next`);
      if (response.ok) {
        const data = await response.json();
        setNextEvent(data.next_event);
      }
    } catch (error) {
      console.error('Error fetching next event:', error);
    } finally {
      setLoading(false);
    }
  };

  const getImpactColor = (impact) => {
    switch (impact) {
      case 'critical': return 'text-red-400';
      case 'high': return 'text-orange-400';
      case 'medium': return 'text-yellow-400';
      case 'low': return 'text-green-400';
      default: return 'text-gray-400';
    }
  };

  if (loading) {
    return (
      <div className={`${compact ? 'p-2' : 'p-4'} bg-gray-800/50 rounded-lg animate-pulse`}>
        <div className="h-4 bg-gray-700 rounded w-3/4 mb-2"></div>
        <div className="h-8 bg-gray-700 rounded w-full"></div>
      </div>
    );
  }

  if (!nextEvent) {
    return null;
  }

  if (compact) {
    return (
      <div className="flex items-center gap-2 p-2 bg-gray-800/50 rounded-lg">
        <span className="text-lg">{nextEvent.icon}</span>
        <div className="flex-1 min-w-0">
          <p className="text-xs text-gray-400 truncate">{nextEvent.name}</p>
          <p className="text-sm font-mono text-white">
            {countdown.days}d {countdown.hours}h {countdown.minutes}m
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 bg-gradient-to-br from-gray-800/80 to-gray-900/80 rounded-xl border border-gray-700/50">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-blue-400" />
          <span className="text-sm font-medium text-gray-300">Next Event</span>
        </div>
        <span className={`text-xs px-2 py-0.5 rounded-full ${getImpactColor(nextEvent.impact)} bg-gray-800`}>
          {nextEvent.impact?.toUpperCase()}
        </span>
      </div>

      {/* Event Name */}
      <div className="flex items-center gap-2 mb-4">
        <span className="text-2xl">{nextEvent.icon}</span>
        <div>
          <h3 className="text-white font-semibold">{nextEvent.name}</h3>
          <p className="text-xs text-gray-400">{nextEvent.date}</p>
        </div>
      </div>

      {/* Countdown */}
      <div className="grid grid-cols-4 gap-2">
        {[
          { label: 'Days', value: countdown.days },
          { label: 'Hours', value: countdown.hours },
          { label: 'Min', value: countdown.minutes },
          { label: 'Sec', value: countdown.seconds }
        ].map((item) => (
          <div key={item.label} className="text-center p-2 bg-gray-800 rounded-lg">
            <span className="text-xl font-bold font-mono text-white">
              {String(item.value).padStart(2, '0')}
            </span>
            <p className="text-xs text-gray-500">{item.label}</p>
          </div>
        ))}
      </div>

      {/* Action */}
      <button className="w-full mt-3 flex items-center justify-center gap-2 p-2 text-sm text-blue-400 hover:bg-blue-500/10 rounded-lg transition-colors">
        <Calendar className="w-4 h-4" />
        View All Events
        <ChevronRight className="w-4 h-4" />
      </button>
    </div>
  );
};

export default EventCountdown;
