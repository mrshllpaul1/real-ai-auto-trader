import React, { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion } from 'framer-motion';
import { 
  Wallet, Sprout, PieChart
} from 'lucide-react';
import { Breadcrumb, useTabKeyboardNav, KeyboardHint, MobileTabsList } from '@/components/HubNavigation';

// Import existing page components
import DeFiWallet from './DeFiWallet';
import YieldFarming from './YieldFarming';
import PortfolioRebalance from './PortfolioRebalance';

const TABS = ['wallet', 'yield', 'rebalance'];

const TAB_LABELS = {
  'wallet': 'Wallet',
  'yield': 'Yield Farming',
  'rebalance': 'Rebalance'
};

const DeFiHub = () => {
  const [activeTab, setActiveTab] = useState('wallet');
  
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
              <TabsTrigger value="wallet" className="data-[state=active]:bg-emerald-500/20 whitespace-nowrap">
                <Wallet className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">Wallet</span>
                <span className="sm:hidden">1</span>
              </TabsTrigger>
              <TabsTrigger value="yield" className="data-[state=active]:bg-green-500/20 whitespace-nowrap">
                <Sprout className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">Yield Farming</span>
                <span className="sm:hidden">2</span>
              </TabsTrigger>
              <TabsTrigger value="rebalance" className="data-[state=active]:bg-blue-500/20 whitespace-nowrap">
                <PieChart className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">Rebalance</span>
                <span className="sm:hidden">3</span>
              </TabsTrigger>
            </TabsList>
          </MobileTabsList>

          <TabsContent value="wallet" className="mt-0">
            <DeFiWallet embedded={true} />
          </TabsContent>

          <TabsContent value="yield" className="mt-0">
            <YieldFarming embedded={true} />
          </TabsContent>

          <TabsContent value="rebalance" className="mt-0">
            <PortfolioRebalance embedded={true} />
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default DeFiHub;
