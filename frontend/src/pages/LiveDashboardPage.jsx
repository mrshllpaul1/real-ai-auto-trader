/**
 * Live Dashboard Page
 * Real-time P&L and portfolio tracking with WebSocket integration
 */

import React from 'react';
import { LivePerformanceDashboard } from '@/components/LivePerformanceDashboard';

const LiveDashboardPage = () => {
  return (
    <div className="min-h-screen bg-[#0A0A0A] p-4 sm:p-6">
      <LivePerformanceDashboard />
    </div>
  );
};

export default LiveDashboardPage;
