import React, { lazy, memo } from 'react';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion } from 'framer-motion';
import { 
  Wallet, Briefcase, PieChart, Layers, Target, LineChart, Activity
} from 'lucide-react';
import { 
  Breadcrumb, 
  useTabState, 
  useTabKeyboardNav, 
  KeyboardHint, 
  MobileTabsList,
  LazyTabContent 
} from '@/components/HubNavigation';

// Lazy load page components for better performance
const SpotTrading = lazy(() => import('./SpotTrading'));
const PositionManagement = lazy(() => import('./PositionManagement'));
const PortfolioDashboard = lazy(() => import('./PortfolioDashboard'));
const AdvancedOrders = lazy(() => import('./AdvancedOrders'));
const OptionsTrading = lazy(() => import('./OptionsTrading'));
const PerpetualFutures = lazy(() => import('./PerpetualFutures'));
const MarketMaker = lazy(() => import('./MarketMaker'));

const TABS = ['spot', 'positions', 'portfolio', 'advanced', 'options', 'perpetuals', 'market-maker'];

const TAB_LABELS = {
  'spot': 'Spot',
  'positions': 'Positions',
  'portfolio': 'Portfolio',
  'advanced': 'Advanced',
  'options': 'Options',
  'perpetuals': 'Perpetuals',
  'market-maker': 'Market Maker'
};

const TAB_CONFIG = [
  { value: 'spot', icon: Wallet, label: 'Spot', color: 'green' },
  { value: 'positions', icon: Briefcase, label: 'Positions', color: 'blue' },
  { value: 'portfolio', icon: PieChart, label: 'Portfolio', color: 'purple' },
  { value: 'advanced', icon: Layers, label: 'Advanced', color: 'amber' },
  { value: 'options', icon: Target, label: 'Options', color: 'cyan' },
  { value: 'perpetuals', icon: LineChart, label: 'Perpetuals', color: 'pink' },
  { value: 'market-maker', icon: Activity, label: 'Market Maker', color: 'orange' },
];

// Memoized tab trigger for performance
const TabTriggerItem = memo(({ value, icon: Icon, label, color }) => (
  <TabsTrigger 
    value={value} 
    className={`data-[state=active]:bg-${color}-500/20 whitespace-nowrap`}
  >
    <Icon className="w-4 h-4 mr-1 md:mr-2" />
    {label}
  </TabsTrigger>
));

TabTriggerItem.displayName = 'TabTriggerItem';

const TradingHub = () => {
  // URL-persisted tab state
  const [activeTab, setActiveTab] = useTabState(TABS, 'spot');
  
  // Enable keyboard navigation
  useTabKeyboardNav(TABS, activeTab, setActiveTab);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4 md:p-6">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-7xl mx-auto"
      >
        {/* Breadcrumb */}
        <Breadcrumb items={[
          { label: 'Trading', href: '/trading' },
          { label: TAB_LABELS[activeTab] }
        ]} />

        <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent">
              Trading Hub
            </h1>
            <p className="text-slate-400 mt-1 text-sm md:text-base">
              All trading functions in one place
            </p>
          </div>
          <div className="flex items-center gap-3">
            <KeyboardHint />
            <Badge variant="outline" className="text-green-400 border-green-400/50">
              <Wallet className="w-3 h-3 mr-1" />
              Kraken Connected
            </Badge>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <MobileTabsList>
            <TabsList className="glass-card flex-nowrap md:flex-wrap h-auto p-1 gap-1 w-max md:w-auto">
              {TAB_CONFIG.map((tab) => (
                <TabTriggerItem key={tab.value} {...tab} />
              ))}
            </TabsList>
          </MobileTabsList>

          {/* Lazy-loaded tab content - only renders active tab */}
          <TabsContent value="spot" className="mt-0">
            <LazyTabContent isActive={activeTab === 'spot'}>
              <SpotTrading embedded={true} />
            </LazyTabContent>
          </TabsContent>

          <TabsContent value="positions" className="mt-0">
            <LazyTabContent isActive={activeTab === 'positions'}>
              <PositionManagement embedded={true} />
            </LazyTabContent>
          </TabsContent>

          <TabsContent value="portfolio" className="mt-0">
            <LazyTabContent isActive={activeTab === 'portfolio'}>
              <PortfolioDashboard embedded={true} />
            </LazyTabContent>
          </TabsContent>

          <TabsContent value="advanced" className="mt-0">
            <LazyTabContent isActive={activeTab === 'advanced'}>
              <AdvancedOrders embedded={true} />
            </LazyTabContent>
          </TabsContent>

          <TabsContent value="options" className="mt-0">
            <LazyTabContent isActive={activeTab === 'options'}>
              <OptionsTrading embedded={true} />
            </LazyTabContent>
          </TabsContent>

          <TabsContent value="perpetuals" className="mt-0">
            <LazyTabContent isActive={activeTab === 'perpetuals'}>
              <PerpetualFutures embedded={true} />
            </LazyTabContent>
          </TabsContent>

          <TabsContent value="market-maker" className="mt-0">
            <LazyTabContent isActive={activeTab === 'market-maker'}>
              <MarketMaker embedded={true} />
            </LazyTabContent>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default TradingHub;
