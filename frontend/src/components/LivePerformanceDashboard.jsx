/**
 * LivePerformanceDashboard - Real-time P&L and portfolio tracking
 * Mobile-responsive with WebSocket integration
 */

import React, { useState, useEffect, useMemo } from 'react';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Activity,
  Brain,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  Wallet,
  BarChart3,
  RefreshCw,
  Wifi,
  WifiOff,
  ChevronRight,
  AlertCircle,
  CheckCircle
} from 'lucide-react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { DataCard } from '@/design-system/components/DataCard';
import { StatWidget } from '@/design-system/components/StatWidget';
import { StatusBadge } from '@/design-system/components/StatusBadge';

const formatCurrency = (value, decimals = 2) => {
  if (value === null || value === undefined) return '$0.00';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};

const formatPercent = (value) => {
  if (value === null || value === undefined) return '0.00%';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
};

export const LivePerformanceDashboard = ({ className }) => {
  const [portfolioData, setPortfolioData] = useState({
    totalValue: 125430.50,
    todayPnL: 2340.25,
    todayPnLPercent: 1.9,
    unrealizedPnL: 8520.75,
    realizedPnL: 15280.00,
    totalReturn: 23.8,
  });

  const [positions, setPositions] = useState([
    { symbol: 'BTC', amount: 1.25, value: 85000, pnl: 5200, pnlPercent: 6.5, signal: 'HOLD' },
    { symbol: 'ETH', amount: 15.5, value: 32000, pnl: 1800, pnlPercent: 5.9, signal: 'BUY' },
    { symbol: 'SOL', amount: 120, value: 8430, pnl: -320, pnlPercent: -3.7, signal: 'HOLD' },
  ]);

  const [signals, setSignals] = useState([
    { id: 1, coin: 'BTC', signal: 'HOLD', confidence: 0.72, time: '2 min ago' },
    { id: 2, coin: 'ETH', signal: 'BUY', confidence: 0.78, time: '5 min ago' },
    { id: 3, coin: 'SOL', signal: 'SELL', confidence: 0.65, time: '12 min ago' },
  ]);

  const [riskMetrics, setRiskMetrics] = useState({
    exposure: 68,
    drawdown: -4.2,
    sharpeRatio: 1.8,
    winRate: 65,
  });

  // WebSocket connection
  const { isConnected, connectionState, lastMessage } = useWebSocket(
    ['portfolio', 'signals', 'prices'],
    {
      onMessage: (data) => {
        if (data.channel === 'portfolio') {
          setPortfolioData(prev => ({ ...prev, ...data.data.portfolio }));
        }
        if (data.channel === 'signals') {
          setSignals(prev => [data.data.signal, ...prev.slice(0, 4)]);
        }
      },
    }
  );

  const getSignalColor = (signal) => {
    switch (signal) {
      case 'BUY': return 'text-green-500 bg-green-500/10';
      case 'SELL': return 'text-red-500 bg-red-500/10';
      default: return 'text-yellow-500 bg-yellow-500/10';
    }
  };

  return (
    <div className={cn('space-y-4 sm:space-y-6', className)}>
      {/* Connection Status */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl sm:text-2xl font-bold">Live Dashboard</h2>
        <div className="flex items-center gap-2">
          {isConnected ? (
            <StatusBadge status="success" label="Live" size="sm" />
          ) : (
            <StatusBadge 
              status={connectionState === 'reconnecting' ? 'loading' : 'error'} 
              label={connectionState === 'reconnecting' ? 'Reconnecting...' : 'Offline'} 
              size="sm" 
            />
          )}
        </div>
      </div>

      {/* Main Stats - Responsive Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <DataCard
          title="Portfolio Value"
          value={formatCurrency(portfolioData.totalValue)}
          icon={Wallet}
          size="sm"
        />
        <DataCard
          title="Today's P&L"
          value={formatCurrency(portfolioData.todayPnL)}
          change={portfolioData.todayPnLPercent}
          trend={portfolioData.todayPnL >= 0 ? 'up' : 'down'}
          variant={portfolioData.todayPnL >= 0 ? 'success' : 'danger'}
          size="sm"
        />
        <DataCard
          title="Unrealized P&L"
          value={formatCurrency(portfolioData.unrealizedPnL)}
          trend={portfolioData.unrealizedPnL >= 0 ? 'up' : 'down'}
          size="sm"
        />
        <DataCard
          title="Total Return"
          value={formatPercent(portfolioData.totalReturn)}
          trend={portfolioData.totalReturn >= 0 ? 'up' : 'down'}
          variant={portfolioData.totalReturn >= 0 ? 'success' : 'danger'}
          size="sm"
        />
      </div>

      {/* Two Column Layout - Stack on Mobile */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        {/* Open Positions */}
        <Card>
          <CardHeader className="pb-2 sm:pb-4">
            <CardTitle className="text-base sm:text-lg flex items-center gap-2">
              <BarChart3 className="h-4 w-4 sm:h-5 sm:w-5" />
              Open Positions
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 sm:space-y-3">
            {positions.map((pos) => (
              <div 
                key={pos.symbol}
                className="flex items-center justify-between p-2 sm:p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
              >
                <div className="flex items-center gap-2 sm:gap-3">
                  <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-primary/10 flex items-center justify-center">
                    <span className="text-xs sm:text-sm font-bold">{pos.symbol}</span>
                  </div>
                  <div>
                    <p className="font-medium text-sm sm:text-base">{pos.amount} {pos.symbol}</p>
                    <p className="text-xs sm:text-sm text-muted-foreground">{formatCurrency(pos.value)}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={cn(
                    'font-mono font-medium text-sm sm:text-base',
                    pos.pnl >= 0 ? 'text-green-500' : 'text-red-500'
                  )}>
                    {pos.pnl >= 0 ? '+' : ''}{formatCurrency(pos.pnl)}
                  </p>
                  <p className={cn(
                    'text-xs sm:text-sm',
                    pos.pnl >= 0 ? 'text-green-500' : 'text-red-500'
                  )}>
                    {formatPercent(pos.pnlPercent)}
                  </p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* AI Signal Feed */}
        <Card>
          <CardHeader className="pb-2 sm:pb-4">
            <CardTitle className="text-base sm:text-lg flex items-center gap-2">
              <Brain className="h-4 w-4 sm:h-5 sm:w-5" />
              AI Signals
              <Badge variant="outline" className="ml-auto text-xs">
                Real-time
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 sm:space-y-3">
            {signals.map((signal) => (
              <div 
                key={signal.id}
                className="flex items-center justify-between p-2 sm:p-3 rounded-lg bg-muted/50"
              >
                <div className="flex items-center gap-2 sm:gap-3">
                  <span className={cn(
                    'px-2 py-1 rounded text-xs sm:text-sm font-medium',
                    getSignalColor(signal.signal)
                  )}>
                    {signal.signal}
                  </span>
                  <span className="font-medium text-sm sm:text-base">{signal.coin}</span>
                </div>
                <div className="text-right">
                  <p className="text-xs sm:text-sm font-mono">
                    {(signal.confidence * 100).toFixed(0)}% conf
                  </p>
                  <p className="text-xs text-muted-foreground">{signal.time}</p>
                </div>
              </div>
            ))}
            <Button variant="ghost" className="w-full text-xs sm:text-sm" size="sm">
              View All Signals
              <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Risk Metrics - Full Width on Mobile */}
      <Card>
        <CardHeader className="pb-2 sm:pb-4">
          <CardTitle className="text-base sm:text-lg flex items-center gap-2">
            <Activity className="h-4 w-4 sm:h-5 sm:w-5" />
            Risk Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 sm:gap-6">
            <StatWidget
              label="Exposure"
              value={riskMetrics.exposure}
              suffix="%"
              size="sm"
            />
            <StatWidget
              label="Max Drawdown"
              value={riskMetrics.drawdown}
              suffix="%"
              trend={riskMetrics.drawdown < -5 ? 'down' : 'neutral'}
              size="sm"
            />
            <StatWidget
              label="Sharpe Ratio"
              value={riskMetrics.sharpeRatio}
              trend={riskMetrics.sharpeRatio > 1.5 ? 'up' : 'neutral'}
              size="sm"
            />
            <StatWidget
              label="Win Rate"
              value={riskMetrics.winRate}
              suffix="%"
              trend={riskMetrics.winRate > 60 ? 'up' : 'down'}
              size="sm"
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default LivePerformanceDashboard;
