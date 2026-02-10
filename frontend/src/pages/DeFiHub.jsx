import React, { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion } from 'framer-motion';
import { 
  Wallet, Sprout, PieChart
} from 'lucide-react';

// Import existing page components
import DeFiWallet from './DeFiWallet';
import YieldFarming from './YieldFarming';
import PortfolioRebalance from './PortfolioRebalance';

const DeFiHub = () => {
  const [activeTab, setActiveTab] = useState('wallet');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4 md:p-6">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-7xl mx-auto"
      >
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent">
              DeFi Hub
            </h1>
            <p className="text-slate-400 mt-1">
              Decentralized finance and yield optimization
            </p>
          </div>
          <Badge variant="outline" className="text-emerald-400 border-emerald-400/50">
            <Sprout className="w-3 h-3 mr-1" />
            DeFi Active
          </Badge>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="glass-card flex-wrap h-auto p-1 gap-1">
            <TabsTrigger value="wallet" className="data-[state=active]:bg-emerald-500/20">
              <Wallet className="w-4 h-4 mr-2" />
              Wallet
            </TabsTrigger>
            <TabsTrigger value="yield" className="data-[state=active]:bg-green-500/20">
              <Sprout className="w-4 h-4 mr-2" />
              Yield Farming
            </TabsTrigger>
            <TabsTrigger value="rebalance" className="data-[state=active]:bg-blue-500/20">
              <PieChart className="w-4 h-4 mr-2" />
              Rebalance
            </TabsTrigger>
          </TabsList>

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
