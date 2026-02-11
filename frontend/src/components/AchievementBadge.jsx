import React, { useState, useEffect } from 'react';
import { Trophy, Star, TrendingUp, Target, Award, Lock } from 'lucide-react';
import { soundManager } from '../utils/soundManager';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL || '';

const AchievementBadge = ({ achievement, earned = false, size = 'md', showDetails = false }) => {
  const sizeClasses = {
    sm: 'w-10 h-10 text-lg',
    md: 'w-14 h-14 text-2xl',
    lg: 'w-20 h-20 text-4xl'
  };

  const bgColor = earned 
    ? 'bg-gradient-to-br from-yellow-500/20 to-orange-500/20 border-yellow-500/50' 
    : 'bg-gray-800/50 border-gray-700';

  return (
    <div className={`relative group ${showDetails ? 'cursor-pointer' : ''}`}>
      {/* Badge */}
      <div className={`
        ${sizeClasses[size]} 
        ${bgColor}
        rounded-xl border-2 flex items-center justify-center
        transition-all duration-300
        ${earned ? 'shadow-lg shadow-yellow-500/20' : 'opacity-60'}
        ${showDetails ? 'group-hover:scale-110' : ''}
      `}>
        {earned ? (
          <span>{achievement.icon}</span>
        ) : (
          <Lock className="w-1/2 h-1/2 text-gray-600" />
        )}
      </div>

      {/* Points badge */}
      {earned && (
        <div className="absolute -top-1 -right-1 px-1.5 py-0.5 bg-yellow-500 rounded-full text-xs font-bold text-black">
          +{achievement.points}
        </div>
      )}

      {/* Tooltip */}
      {showDetails && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-3 shadow-xl min-w-[200px]">
            <p className="font-semibold text-white text-sm">{achievement.name}</p>
            <p className="text-xs text-gray-400 mt-1">{achievement.description}</p>
            <div className="flex items-center gap-2 mt-2">
              <Star className="w-3 h-3 text-yellow-400" />
              <span className="text-xs text-yellow-400">{achievement.points} points</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export const AchievementNotification = ({ achievement, onClose }) => {
  useEffect(() => {
    soundManager.playAchievement();
    const timer = setTimeout(onClose, 5000);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div className="fixed top-4 right-4 z-50 animate-slide-in-right">
      <div className="bg-gradient-to-r from-yellow-900/90 to-orange-900/90 border border-yellow-500/50 rounded-xl p-4 shadow-2xl max-w-sm">
        <div className="flex items-start gap-3">
          <div className="p-2 bg-yellow-500/20 rounded-lg text-3xl">
            {achievement.icon}
          </div>
          <div className="flex-1">
            <p className="text-xs text-yellow-400 font-medium">Achievement Unlocked!</p>
            <p className="text-white font-semibold">{achievement.name}</p>
            <p className="text-sm text-gray-300 mt-1">{achievement.description}</p>
            <div className="flex items-center gap-2 mt-2">
              <Trophy className="w-4 h-4 text-yellow-400" />
              <span className="text-sm text-yellow-400">+{achievement.points} points</span>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            ×
          </button>
        </div>
      </div>
    </div>
  );
};

export const AchievementsGrid = ({ userId = 'default_user' }) => {
  const [achievements, setAchievements] = useState([]);
  const [earned, setEarned] = useState([]);
  const [stats, setStats] = useState({ totalPoints: 0, level: 1 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAchievements();
  }, [userId]);

  const fetchAchievements = async () => {
    try {
      const [allRes, userRes] = await Promise.all([
        fetch(`${BACKEND_URL}/api/achievements/list`),
        fetch(`${BACKEND_URL}/api/achievements/user?user_id=${userId}`)
      ]);

      if (allRes.ok) {
        const allData = await allRes.json();
        setAchievements(allData.achievements || []);
      }

      if (userRes.ok) {
        const userData = await userRes.json();
        setEarned(userData.earned || []);
        setStats({
          totalPoints: userData.total_points || 0,
          level: userData.level || 1
        });
      }
    } catch (error) {
      console.error('Error fetching achievements:', error);
    } finally {
      setLoading(false);
    }
  };

  const earnedIds = earned.map(e => e.id);

  if (loading) {
    return (
      <div className="grid grid-cols-4 gap-4 animate-pulse">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="w-14 h-14 bg-gray-800 rounded-xl" />
        ))}
      </div>
    );
  }

  return (
    <div>
      {/* Stats Header */}
      <div className="flex items-center justify-between mb-4 p-3 bg-gradient-to-r from-yellow-900/20 to-orange-900/20 rounded-lg border border-yellow-500/20">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-yellow-500/20 rounded-lg">
            <Trophy className="w-5 h-5 text-yellow-400" />
          </div>
          <div>
            <p className="text-xs text-gray-400">Level {stats.level}</p>
            <p className="text-lg font-bold text-white">{stats.totalPoints} Points</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-400">Progress</p>
          <p className="text-sm text-white">{earned.length}/{achievements.length} Unlocked</p>
        </div>
      </div>

      {/* Achievements Grid */}
      <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 gap-3">
        {achievements.map((ach) => (
          <AchievementBadge
            key={ach.id}
            achievement={ach}
            earned={earnedIds.includes(ach.id)}
            showDetails
          />
        ))}
      </div>
    </div>
  );
};

export default AchievementBadge;
