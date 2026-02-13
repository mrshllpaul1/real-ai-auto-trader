import React, { lazy, memo } from 'react';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion } from 'framer-motion';
import { BarChart3, Calendar, Gem, LineChart, Shield } from 'lucide-react';
import { 
  Breadcrumb, useTabState, useTabKeyboardNav, KeyboardHint, MobileTabsList, LazyTabContent 
} from '@/components/HubNavigation';
import { PageLoadingSkeleton } from '../components/LoadingSkeleton';

const BacktestEngine = lazy(() => import('./BacktestEngine'));
const YearlyBacktest = lazy(() => import('./YearlyBacktest'));
const GemBacktester = lazy(() => import('./GemBacktester'));
const Analytics = lazy(() => import('./Analytics'));
const RiskAnalyzer = lazy(() => import('./RiskAnalyzer'));

const TABS = ['engine', 'yearly', 'gems', 'analytics', 'risk'];
const TAB_LABELS = { 'engine': 'Backtest', 'yearly': 'Yearly', 'gems': 'Gems', 'analytics': 'Analytics', 'risk': 'Risk' };

const TAB_CONFIG = [
  { value: 'engine', icon: BarChart3, label: 'Backtest', color: 'blue' },
  { value: 'yearly', icon: Calendar, label: 'Yearly', color: 'purple' },
  { value: 'gems', icon: Gem, label: 'Gems', color: 'amber' },
  { value: 'analytics', icon: LineChart, label: 'Analytics', color: 'green' },
  { value: 'risk', icon: Shield, label: 'Risk', color: 'red' },
];

const TabTriggerItem = memo(({ value, icon: Icon, label, color }) => (
  <TabsTrigger value={value} className={`data-[state=active]:bg-${color}-500/20 whitespace-nowrap`}>
    <Icon className="w-4 h-4 mr-1 md:mr-2" />{label}
  </TabsTrigger>
));
TabTriggerItem.displayName = 'TabTriggerItem';

const BacktestHub = () => {
  const [activeTab, setActiveTab] = useTabState(TABS, 'engine');
  useTabKeyboardNav(TABS, activeTab, setActiveTab);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4 md:p-6">
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="max-w-7xl mx-auto">
        <Breadcrumb items={[{ label: 'Backtest & Analysis', href: '/backtest' }, { label: TAB_LABELS[activeTab] }]} />
        <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
              Backtest & Analysis
            </h1>
            <p className="text-slate-400 mt-1 text-sm md:text-base">Test strategies and analyze performance</p>
          </div>
          <div className="flex items-center gap-3">
            <KeyboardHint />
            <Badge variant="outline" className="text-blue-400 border-blue-400/50">
              <BarChart3 className="w-3 h-3 mr-1" />2020-2026 Data
            </Badge>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <MobileTabsList>
            <TabsList className="glass-card flex-nowrap md:flex-wrap h-auto p-1 gap-1 w-max md:w-auto">
              {TAB_CONFIG.map((tab) => <TabTriggerItem key={tab.value} {...tab} />)}
            </TabsList>
          </MobileTabsList>

          <TabsContent value="engine" className="mt-0">
            <LazyTabContent isActive={activeTab === 'engine'}><BacktestEngine embedded={true} /></LazyTabContent>
          </TabsContent>
          <TabsContent value="yearly" className="mt-0">
            <LazyTabContent isActive={activeTab === 'yearly'}><YearlyBacktest embedded={true} /></LazyTabContent>
          </TabsContent>
          <TabsContent value="gems" className="mt-0">
            <LazyTabContent isActive={activeTab === 'gems'}><GemBacktester embedded={true} /></LazyTabContent>
          </TabsContent>
          <TabsContent value="analytics" className="mt-0">
            <LazyTabContent isActive={activeTab === 'analytics'}><Analytics embedded={true} /></LazyTabContent>
          </TabsContent>
          <TabsContent value="risk" className="mt-0">
            <LazyTabContent isActive={activeTab === 'risk'}><RiskAnalyzer embedded={true} /></LazyTabContent>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default BacktestHub;
