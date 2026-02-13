import React, { lazy, memo } from 'react';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion } from 'framer-motion';
import { 
  Wallet, Sprout, PieChart
} from 'lucide-react';
import { 
  Breadcrumb, 
  useTabState, 
  useTabKeyboardNav, 
  KeyboardHint, 
  MobileTabsList,
  LazyTabContent 
} from '@/components/HubNavigation';
import { PageLoadingSkeleton } from '../components/LoadingSkeleton';

// Lazy load page components for better performance
const DeFiWallet = lazy(() => import('./DeFiWallet'));
const YieldFarming = lazy(() => import('./YieldFarming'));
const PortfolioRebalance = lazy(() => import('./PortfolioRebalance'));

const TABS = ['wallet', 'yield', 'rebalance'];

const TAB_LABELS = {
  'wallet': 'Wallet',
  'yield': 'Yield Farming',
  'rebalance': 'Rebalance'
};

const TAB_CONFIG = [
  { value: 'wallet', icon: Wallet, label: 'Wallet', color: 'emerald' },
  { value: 'yield', icon: Sprout, label: 'Yield Farming', color: 'green' },
  { value: 'rebalance', icon: PieChart, label: 'Rebalance', color: 'blue' },
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

const DeFiHub = () => {
  // URL-persisted tab state
  const [activeTab, setActiveTab] = useTabState(TABS, 'wallet');
  
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
          { label: 'DeFi', href: '/defi' },
          { label: TAB_LABELS[activeTab] }
        ]} />

        <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent">
              DeFi Hub
            </h1>
            <p className="text-slate-400 mt-1 text-sm md:text-base">
              Decentralized finance and yield optimization
            </p>
          </div>
          <div className="flex items-center gap-3">
            <KeyboardHint />
            <Badge variant="outline" className="text-emerald-400 border-emerald-400/50">
              <Sprout className="w-3 h-3 mr-1" />
              DeFi Active
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
          <TabsContent value="wallet" className="mt-0">
            <LazyTabContent isActive={activeTab === 'wallet'}>
              <DeFiWallet embedded={true} />
            </LazyTabContent>
          </TabsContent>

          <TabsContent value="yield" className="mt-0">
            <LazyTabContent isActive={activeTab === 'yield'}>
              <YieldFarming embedded={true} />
            </LazyTabContent>
          </TabsContent>

          <TabsContent value="rebalance" className="mt-0">
            <LazyTabContent isActive={activeTab === 'rebalance'}>
              <PortfolioRebalance embedded={true} />
            </LazyTabContent>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default DeFiHub;
