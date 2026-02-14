import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  TrendingUp, TrendingDown, DollarSign, Activity, Wallet, Target,
  Play, Square, Settings, Zap, PieChart, Bell, Waves, LineChart,
  RefreshCw, ArrowUpDown, Shield, MessageCircle, FlaskConical,
  Rocket, Brain, BarChart3, AlertTriangle, CheckCircle, ArrowRight,
  Bot, Cpu, Newspaper, ShoppingCart, Search
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { motion } from 'framer-motion';
import { PieChart as RechartsPieChart, Pie, Cell, ResponsiveContainer, AreaChart, Area, Tooltip } from 'recharts';
import api, { tradingAPI, marketAPI, clearAllCacheAndRefresh } from '../services/api';
import { toast } from 'sonner';
import MarketOverview from '../components/MarketOverview';
import { CardSkeleton, TableSkeleton } from '../components/LoadingSkeleton';

// Simplified state management
const ComponentType = {
  MASTER_ORCHESTRATOR: 'master_orchestrator',
  TETHYS_AUTOPILOT: 'tethys_autopilot',
};

// Coin color mapping for avatars and charts
const COIN_COLORS = {
  BTC: '#F7931A', USD: '#85BB65', ETH: '#627EEA', SOL: '#9945FF',
  DOT: '#E6007A', AAVE: '#B6509E', UNI: '#FF007A', XRP: '#00AAE4',
  ADA: '#0D1E30', MATIC: '#8247E5', LINK: '#2A5ADA', AVAX: '#E84142',
  ATOM: '#2E3148', SUI: '#4DA2FF', APT: '#000000', DOGE: '#C2A633',
  SHIB: '#FFA409', ARB: '#28A0F0', OP: '#FF0420', FTM: '#1969FF',
  DEFAULT: '#6366F1',
};

const getCoinColor = (symbol) => COIN_COLORS[symbol?.toUpperCase()] || COIN_COLORS.DEFAULT;

// Generate synthetic sparkline data based on portfolio change
const generateSparkline = (currentValue, change24h) => {
  const points = 24;
  const baseValue = currentValue / (1 + (change24h || 0) / 100);
  const data = [];
  for (let i = 0; i < points; i++) {
    const progress = i / (points - 1);
    const noise = (Math.random() - 0.5) * currentValue * 0.01;
    const value = baseValue + (currentValue - baseValue) * progress + noise;
    data.push({ time: i, value: Math.max(0, value) });
  }
  return data;
};

// Loading Skeleton
const CommandCenterSkeleton = () => (
  <div className="p-6 space-y-6">
    <div className="flex items-center justify-between">
      <div className="space-y-2">
        <div className="w-48 h-8 rounded bg-gray-800 animate-pulse" />
        <div className="w-64 h-4 rounded bg-gray-800 animate-pulse" />
      </div>
      <div className="w-24 h-10 rounded bg-gray-800 animate-pulse" />
    </div>
    <div className="flex gap-2 border-b border-gray-800 pb-2">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="w-32 h-10 rounded bg-gray-800 animate-pulse" />
      ))}
    </div>
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <CardSkeleton /><CardSkeleton /><CardSkeleton />
    </div>
    <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
      <div className="w-40 h-5 rounded bg-gray-800 mb-4 animate-pulse" />
      <TableSkeleton rows={4} />
    </div>
  </div>
);

// Coin Avatar component
const CoinAvatar = ({ symbol, size = 'md' }) => {
  const color = getCoinColor(symbol);
  const sizeClasses = size === 'sm' ? 'w-7 h-7 text-[10px]' : 'w-9 h-9 text-xs';
  return (
    <div 
      className={`${sizeClasses} rounded-full flex items-center justify-center font-bold text-white shadow-lg`}
      style={{ backgroundColor: color, boxShadow: `0 0 12px ${color}40` }}
    >
      {(symbol || '?').slice(0, 3)}
    </div>
  );
};

// Mini Sparkline for portfolio card
const MiniSparkline = ({ data, color = '#06b6d4', height = 40 }) => (
  <ResponsiveContainer width="100%" height={height}>
    <AreaChart data={data} margin={{ top: 2, right: 0, left: 0, bottom: 0 }}>
      <defs>
        <linearGradient id="sparkGradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity={0.3} />
          <stop offset="100%" stopColor={color} stopOpacity={0} />
        </linearGradient>
      </defs>
      <Area 
        type="monotone" 
        dataKey="value" 
        stroke={color} 
        strokeWidth={1.5} 
        fill="url(#sparkGradient)" 
        dot={false}
        isAnimationActive={true}
      />
    </AreaChart>
  </ResponsiveContainer>
);

// Portfolio Donut Chart
const PortfolioDonut = ({ holdings }) => {
  const [activeIndex, setActiveIndex] = useState(null);
  
  if (!holdings || holdings.length === 0) return null;

  // Prepare data - top 6 + others
  const sorted = [...holdings].sort((a, b) => (b.value_usd || 0) - (a.value_usd || 0));
  const top = sorted.slice(0, 6);
  const othersValue = sorted.slice(6).reduce((sum, h) => sum + (h.value_usd || 0), 0);
  
  const chartData = top.map(h => ({
    name: h.symbol || 'Unknown',
    value: h.value_usd || 0,
    color: getCoinColor(h.symbol),
  }));
  
  if (othersValue > 0) {
    chartData.push({ name: 'Others', value: othersValue, color: '#374151' });
  }

  const total = chartData.reduce((s, d) => s + d.value, 0);

  return (
    <Card className="bg-gray-900/50 border-gray-800">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-gray-400 flex items-center gap-2">
          <PieChart className="w-4 h-4 text-cyan-400" /> Portfolio Allocation
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4">
          {/* Donut Chart */}
          <div className="relative w-36 h-36 flex-shrink-0">
            <ResponsiveContainer width="100%" height="100%">
              <RechartsPieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={35}
                  outerRadius={60}
                  paddingAngle={2}
                  dataKey="value"
                  onMouseEnter={(_, idx) => setActiveIndex(idx)}
                  onMouseLeave={() => setActiveIndex(null)}
                  animationBegin={0}
                  animationDuration={800}
                >
                  {chartData.map((entry, index) => (
                    <Cell 
                      key={entry.name} 
                      fill={entry.color} 
                      stroke="transparent"
                      opacity={activeIndex === null || activeIndex === index ? 1 : 0.4}
                    />
                  ))}
                </Pie>
                <Tooltip 
                  content={({ active, payload }) => {
                    if (active && payload?.[0]) {
                      const d = payload[0].payload;
                      return (
                        <div className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 shadow-xl">
                          <p className="text-white text-xs font-bold">{d.name}</p>
                          <p className="text-slate-300 text-xs">${d.value.toFixed(2)} ({((d.value / total) * 100).toFixed(1)}%)</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
              </RechartsPieChart>
            </ResponsiveContainer>
            {/* Center label */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="text-[10px] text-gray-500">Total</div>
                <div className="text-xs font-bold text-white">${total.toFixed(0)}</div>
              </div>
            </div>
          </div>

          {/* Legend */}
          <div className="flex-1 grid grid-cols-2 gap-x-3 gap-y-1.5">
            {chartData.map((item) => (
              <div key={item.name} className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: item.color }} />
                <span className="text-xs text-gray-400 truncate">{item.name}</span>
                <span className="text-xs text-white font-medium ml-auto">{((item.value / total) * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Quick Actions Panel
const QuickActionsPanel = () => {
  const navigate = useNavigate();
  
  const actions = [
    { label: 'Buy/Sell', icon: ShoppingCart, path: '/trading', color: 'from-emerald-500/20 to-green-500/10 border-emerald-500/30', iconColor: 'text-emerald-400' },
    { label: 'AI Signal', icon: Zap, path: '/ai', color: 'from-violet-500/20 to-purple-500/10 border-violet-500/30', iconColor: 'text-violet-400' },
    { label: 'Backtest', icon: BarChart3, path: '/backtest', color: 'from-blue-500/20 to-cyan-500/10 border-blue-500/30', iconColor: 'text-blue-400' },
    { label: 'News', icon: Newspaper, path: '/news', color: 'from-pink-500/20 to-rose-500/10 border-pink-500/30', iconColor: 'text-pink-400' },
    { label: 'Auto Trade', icon: Bot, path: '/ai', color: 'from-amber-500/20 to-orange-500/10 border-amber-500/30', iconColor: 'text-amber-400' },
    { label: 'Settings', icon: Settings, path: '/settings', color: 'from-slate-500/20 to-gray-500/10 border-slate-500/30', iconColor: 'text-slate-400' },
  ];

  return (
    <Card className="bg-gray-900/50 border-gray-800">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-gray-400 flex items-center gap-2">
          <Zap className="w-4 h-4 text-amber-400" /> Quick Actions
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
          {actions.map((action) => (
            <motion.button
              key={action.label}
              whileHover={{ scale: 1.05, y: -2 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => navigate(action.path)}
              className={`flex flex-col items-center gap-1.5 p-3 rounded-xl bg-gradient-to-br ${action.color} border transition-all duration-200 hover:shadow-lg`}
            >
              <action.icon className={`w-5 h-5 ${action.iconColor}`} />
              <span className="text-[11px] font-medium text-gray-300">{action.label}</span>
            </motion.button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

// Dashboard Tab - Enhanced with donut chart, sparkline, coin icons, quick actions
const DashboardTab = ({ portfolio, krakenPortfolio, prices }) => {
  const sparklineData = generateSparkline(
    krakenPortfolio?.total_value_usd || 0, 
    krakenPortfolio?.change_24h || 0
  );
  const sparkColor = (krakenPortfolio?.change_24h || 0) >= 0 ? '#10b981' : '#ef4444';

  return (
    <div className="space-y-5">
      {/* Quick Actions */}
      <QuickActionsPanel />

      {/* Portfolio Cards with Sparkline */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-gradient-to-br from-cyan-500/10 to-blue-500/10 border-cyan-500/20">
          <CardHeader className="pb-1">
            <CardTitle className="text-sm font-medium text-gray-400 flex items-center gap-2">
              <Wallet className="w-4 h-4" /> Kraken Portfolio
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="flex items-end justify-between">
              <div>
                <div className="text-2xl font-bold text-white">
                  ${(krakenPortfolio?.total_value_usd ?? 0).toFixed(2)}
                </div>
                <div className="text-xs text-gray-400">
                  {krakenPortfolio?.holdings_count || krakenPortfolio?.holdings?.length || 0} assets
                </div>
              </div>
              <div className="w-24 h-10">
                <MiniSparkline data={sparklineData} color={sparkColor} height={40} />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 border-green-500/20">
          <CardHeader className="pb-1">
            <CardTitle className="text-sm font-medium text-gray-400 flex items-center gap-2">
              <TrendingUp className="w-4 h-4" /> 24h Change
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className={`text-2xl font-bold ${(krakenPortfolio?.change_24h || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {krakenPortfolio?.change_24h >= 0 ? '+' : ''}{(krakenPortfolio?.change_24h ?? 0).toFixed(2)}%
            </div>
            <div className="mt-1 flex items-center gap-1">
              {(krakenPortfolio?.change_24h || 0) >= 0 
                ? <TrendingUp className="w-3 h-3 text-green-400" /> 
                : <TrendingDown className="w-3 h-3 text-red-400" />
              }
              <span className="text-xs text-gray-500">last 24 hours</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 border-purple-500/20">
          <CardHeader className="pb-1">
            <CardTitle className="text-sm font-medium text-gray-400 flex items-center gap-2">
              <Activity className="w-4 h-4" /> AI Budget
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="text-2xl font-bold text-white">
              ${(portfolio?.current_value ?? 0).toFixed(2)}
            </div>
            <div className="text-xs text-gray-400">Isolated trading budget</div>
          </CardContent>
        </Card>
      </div>

      {/* Portfolio Allocation Donut + Market Overview side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <PortfolioDonut holdings={krakenPortfolio?.holdings} />
        <MarketOverview />
      </div>

      {/* Holdings Table with Coin Icons */}
      {krakenPortfolio?.holdings?.length > 0 && (
        <Card className="bg-gray-900/50 border-gray-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-white flex items-center gap-2">
              <Wallet className="w-4 h-4 text-cyan-400" /> Holdings
              <Badge variant="outline" className="ml-2 text-xs text-gray-400 border-gray-700">
                {krakenPortfolio.holdings.length} assets
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-500 border-b border-gray-800 text-xs uppercase tracking-wider">
                    <th className="text-left py-2.5 pl-1">Asset</th>
                    <th className="text-right py-2.5">Amount</th>
                    <th className="text-right py-2.5">Value</th>
                    <th className="text-right py-2.5">Allocation</th>
                    <th className="text-right py-2.5 pr-1">24h</th>
                  </tr>
                </thead>
                <tbody>
                  {krakenPortfolio.holdings.slice(0, 12).map((h, i) => {
                    const total = krakenPortfolio.total_value_usd || 1;
                    const alloc = ((h.value_usd || 0) / total * 100);
                    return (
                      <motion.tr 
                        key={i} 
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.03 }}
                        className="border-b border-gray-800/40 hover:bg-gray-800/30 transition-colors"
                      >
                        <td className="py-2.5 pl-1">
                          <div className="flex items-center gap-2.5">
                            <CoinAvatar symbol={h.symbol} size="sm" />
                            <div>
                              <span className="text-white font-medium text-sm">{h.symbol}</span>
                            </div>
                          </div>
                        </td>
                        <td className="py-2.5 text-right text-gray-300 font-mono text-xs">
                          {(h?.amount ?? 0).toFixed(4)}
                        </td>
                        <td className="py-2.5 text-right text-white font-medium">
                          ${(h?.value_usd ?? 0).toFixed(2)}
                        </td>
                        <td className="py-2.5 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <div className="w-16 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                              <div 
                                className="h-full rounded-full" 
                                style={{ 
                                  width: `${Math.min(alloc, 100)}%`, 
                                  backgroundColor: getCoinColor(h.symbol) 
                                }} 
                              />
                            </div>
                            <span className="text-xs text-gray-400 w-10 text-right">{alloc.toFixed(1)}%</span>
                          </div>
                        </td>
                        <td className={`py-2.5 text-right pr-1 font-medium text-sm ${(h.change_24h || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {(h?.change_24h || 0) >= 0 ? '+' : ''}{(h?.change_24h ?? 0).toFixed(2)}%
                        </td>
                      </motion.tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

const GrowthTab = ({ growthStatus, onToggleAutopilot }) => (
  <div className="space-y-6">
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <Card className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 border-green-500/20">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-gray-400">
            <Rocket className="w-4 h-4 inline mr-2" />Goal: $500 → $100K
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-400">
            {((growthStatus?.current_value || 500) / 100000 * 100).toFixed(2)}%
          </div>
          <div className="text-sm text-gray-400">Progress to goal</div>
        </CardContent>
      </Card>

      <Card className="bg-gray-900/50 border-gray-800">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-gray-400">Current Value</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-white">
            ${(growthStatus?.current_value ?? 0).toFixed(2) || '500.00'}
          </div>
        </CardContent>
      </Card>

      <Card className="bg-gray-900/50 border-gray-800">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-gray-400">Total P/L</CardTitle>
        </CardHeader>
        <CardContent>
          <div className={`text-2xl font-bold ${(growthStatus?.total_pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {growthStatus?.total_pnl >= 0 ? '+' : ''}${(growthStatus?.total_pnl ?? 0).toFixed(2) || '0.00'}
          </div>
        </CardContent>
      </Card>

      <Card className="bg-gray-900/50 border-gray-800">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-gray-400">Autopilot</CardTitle>
        </CardHeader>
        <CardContent>
          <Button
            onClick={onToggleAutopilot}
            className={growthStatus?.autopilot_active 
              ? 'bg-red-600 hover:bg-red-700' 
              : 'bg-green-600 hover:bg-green-700'}
          >
            {growthStatus?.autopilot_active ? <Square className="w-4 h-4 mr-2" /> : <Play className="w-4 h-4 mr-2" />}
            {growthStatus?.autopilot_active ? 'Stop' : 'Start'}
          </Button>
        </CardContent>
      </Card>
    </div>

    <Card className="bg-gray-900/50 border-gray-800">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <Target className="w-5 h-5 text-cyan-400" />
          Growth Strategy
        </CardTitle>
      </CardHeader>
      <CardContent className="text-gray-300 space-y-2">
        <p>• Target: 200x returns ($500 → $100,000)</p>
        <p>• Strategy: AI-powered gem hunting + momentum trading</p>
        <p>• Risk: Aggressive (high reward potential)</p>
        <p>• Auto-rebalancing enabled when autopilot is active</p>
      </CardContent>
    </Card>
  </div>
);

const MasterTab = ({ orchestratorStatus, onToggleOrchestrator }) => (
  <div className="space-y-6">
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <Card className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 border-purple-500/20">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-gray-400">
            <Brain className="w-4 h-4 inline mr-2" />Master Orchestrator
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Badge className={orchestratorStatus?.is_active ? 'bg-green-500' : 'bg-gray-600'}>
            {orchestratorStatus?.is_active ? 'ACTIVE' : 'STOPPED'}
          </Badge>
        </CardContent>
      </Card>

      <Card className="bg-gray-900/50 border-gray-800">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-gray-400">Mode</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-xl font-bold text-cyan-400 capitalize">
            {orchestratorStatus?.mode?.replace('_', ' ') || 'Auto'}
          </div>
        </CardContent>
      </Card>

      <Card className="bg-gray-900/50 border-gray-800">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-gray-400">Executed Trades</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-white">
            {orchestratorStatus?.stats?.executed_trades || 0}
          </div>
        </CardContent>
      </Card>

      <Card className="bg-gray-900/50 border-gray-800">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-gray-400">Control</CardTitle>
        </CardHeader>
        <CardContent>
          <Button
            onClick={onToggleOrchestrator}
            className={orchestratorStatus?.is_active 
              ? 'bg-red-600 hover:bg-red-700' 
              : 'bg-cyan-600 hover:bg-cyan-700'}
          >
            {orchestratorStatus?.is_active ? 'Stop' : 'Start'} Orchestrator
          </Button>
        </CardContent>
      </Card>
    </div>
  </div>
);

const UpgradesTab = ({ upgradesStatus }) => (
  <div className="space-y-6">
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {[
        { name: 'Whale Tracker', icon: Waves, status: upgradesStatus?.features?.whale_tracking?.is_monitoring },
        { name: 'Sentiment', icon: MessageCircle, status: upgradesStatus?.features?.sentiment?.is_monitoring },
        { name: 'Arbitrage', icon: Zap, status: upgradesStatus?.features?.arbitrage?.is_monitoring },
        { name: 'Trailing Stops', icon: Target, status: upgradesStatus?.features?.trailing_stops?.is_monitoring },
        { name: 'Rebalancer', icon: PieChart, status: upgradesStatus?.features?.rebalancer?.enabled },
        { name: 'A/B Testing', icon: FlaskConical, status: upgradesStatus?.features?.ab_testing?.is_monitoring },
        { name: 'Backtest', icon: LineChart, status: upgradesStatus?.features?.backtest?.available },
        { name: 'Notifications', icon: Bell, status: upgradesStatus?.features?.push_notifications?.active },
      ].map((feature, idx) => (
        <Card key={idx} className="bg-gray-900/50 border-gray-800">
          <CardContent className="pt-4 text-center">
            <feature.icon className={`w-8 h-8 mx-auto mb-2 ${feature.status ? 'text-green-400' : 'text-gray-500'}`} />
            <div className="text-sm text-white">{feature.name}</div>
            <Badge className={`mt-2 ${feature.status ? 'bg-green-500/20 text-green-400' : 'bg-gray-600/20 text-gray-400'}`}>
              {feature.status ? 'Active' : 'Inactive'}
            </Badge>
          </CardContent>
        </Card>
      ))}
    </div>

    <Card className="bg-gray-900/50 border-gray-800">
      <CardHeader>
        <CardTitle className="text-white">Quick Actions</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-wrap gap-3">
        <Button onClick={() => window.location.href = '/settings'} variant="outline" className="border-cyan-500 text-cyan-400">
          <Settings className="w-4 h-4 mr-2" /> Manage Settings
        </Button>
        <Button onClick={() => window.location.href = '/trading'} variant="outline" className="border-green-500 text-green-400">
          <ArrowUpDown className="w-4 h-4 mr-2" /> Spot Trading
        </Button>
        <Button onClick={() => window.location.href = '/ai'} variant="outline" className="border-purple-500 text-purple-400">
          <BarChart3 className="w-4 h-4 mr-2" /> AI & Strategy
        </Button>
      </CardContent>
    </Card>
  </div>
);

const CommandCenter = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(true);
  const [portfolio, setPortfolio] = useState(null);
  const [krakenPortfolio, setKrakenPortfolio] = useState(null);
  const [prices, setPrices] = useState({});
  const [growthStatus, setGrowthStatus] = useState(null);
  const [orchestratorStatus, setOrchestratorStatus] = useState(null);
  const [upgradesStatus, setUpgradesStatus] = useState(null);

  const [orchestratorPersisted, setOrchestratorPersisted] = useState(false);
  const [autopilotPersisted, setAutopilotPersisted] = useState(false);
  
  const updateComponentState = async (component, isRunning) => {
    const baseUrl = import.meta.env.VITE_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL || '';
    try {
      await fetch(`${baseUrl}/api/system-state/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ component, user_id: 'default', is_running: isRunning, metadata: {} })
      });
      return true;
    } catch (e) {
      console.error('Failed to update state:', e);
      return false;
    }
  };
  
  const setOrchestratorState = async (running) => {
    if (await updateComponentState(ComponentType.MASTER_ORCHESTRATOR, running)) {
      setOrchestratorPersisted(running);
    }
  };
  
  const setAutopilotState = async (running) => {
    if (await updateComponentState(ComponentType.TETHYS_AUTOPILOT, running)) {
      setAutopilotPersisted(running);
    }
  };

  const fetchData = useCallback(async (forceRefresh = false) => {
    try {
      if (forceRefresh) {
        clearAllCacheAndRefresh();
        toast.info('Refreshing data...');
      }
      
      const [portfolioRes, krakenRes, pricesRes, growthRes, orchRes, upgradesRes] = await Promise.allSettled([
        tradingAPI.getPortfolio(),
        tradingAPI.getKrakenPortfolio(),
        marketAPI.getPrices('bitcoin,ethereum,solana'),
        api.get('/growth/status'),
        api.get('/master/status'),
        api.get('/upgrades/status')
      ]);

      if (portfolioRes.status === 'fulfilled') setPortfolio(portfolioRes.value.data);
      if (krakenRes.status === 'fulfilled') setKrakenPortfolio(krakenRes.value.data);
      if (pricesRes.status === 'fulfilled') setPrices(pricesRes.value.data);
      if (growthRes.status === 'fulfilled') setGrowthStatus(growthRes.value.data);
      if (orchRes.status === 'fulfilled') setOrchestratorStatus(orchRes.value.data);
      if (upgradesRes.status === 'fulfilled') setUpgradesStatus(upgradesRes.value.data);
      
      if (forceRefresh) toast.success('Data refreshed!');
    } catch (error) {
      console.error('Error loading data:', error);
      if (forceRefresh) toast.error('Failed to refresh data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const toggleAutopilot = async () => {
    try {
      const isCurrentlyActive = autopilotPersisted || growthStatus?.autopilot_active;
      if (isCurrentlyActive) {
        await api.post('/growth/stop');
        await setAutopilotState(false);
      } else {
        await api.post('/growth/start');
        await setAutopilotState(true);
      }
      fetchData();
      toast.success(isCurrentlyActive ? 'Autopilot stopped' : 'Autopilot started');
    } catch (error) {
      toast.error('Failed to toggle autopilot');
    }
  };

  const toggleOrchestrator = async () => {
    try {
      const isCurrentlyActive = orchestratorPersisted || orchestratorStatus?.is_active;
      if (isCurrentlyActive) {
        await api.post('/master/stop');
        await setOrchestratorState(false);
      } else {
        await api.post('/master/start');
        await setOrchestratorState(true);
      }
      fetchData();
      toast.success(isCurrentlyActive ? 'Orchestrator stopped' : 'Orchestrator started');
    } catch (error) {
      toast.error('Failed to toggle orchestrator');
    }
  };

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: Activity },
    { id: 'growth', label: '$500→$100K', icon: Rocket },
    { id: 'master', label: 'Master Control', icon: Brain },
    { id: 'upgrades', label: 'Upgrades', icon: Zap },
  ];

  if (loading) return <CommandCenterSkeleton />;

  return (
    <div className="p-6 space-y-6" data-testid="command-center">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Command Center</h1>
          <p className="text-gray-400">Unified trading control panel</p>
        </div>
        <Button onClick={() => fetchData(true)} variant="outline" className="border-gray-700">
          <RefreshCw className="w-4 h-4 mr-2" /> Refresh
        </Button>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-gray-800 pb-2 overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-t-lg transition-colors whitespace-nowrap ${
              activeTab === tab.id
                ? 'bg-cyan-500/20 text-cyan-400 border-b-2 border-cyan-400'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
      >
        {activeTab === 'dashboard' && (
          <DashboardTab portfolio={portfolio} krakenPortfolio={krakenPortfolio} prices={prices} />
        )}
        {activeTab === 'growth' && (
          <GrowthTab growthStatus={growthStatus} onToggleAutopilot={toggleAutopilot} />
        )}
        {activeTab === 'master' && (
          <MasterTab orchestratorStatus={orchestratorStatus} onToggleOrchestrator={toggleOrchestrator} />
        )}
        {activeTab === 'upgrades' && (
          <UpgradesTab upgradesStatus={upgradesStatus} />
        )}
      </motion.div>
    </div>
  );
};

export default CommandCenter;
