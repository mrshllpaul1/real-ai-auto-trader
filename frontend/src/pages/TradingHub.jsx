import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion } from 'framer-motion';
import { 
  Wallet, Briefcase, PieChart, Layers, Target, LineChart, Activity,
  RefreshCw, TrendingUp, TrendingDown, DollarSign, ArrowUpRight, ArrowDownRight
} from 'lucide-react';
import { toast } from 'sonner';

// Import existing page components as sub-components
import SpotTrading from './SpotTrading';
import PositionManagement from './PositionManagement';
import PortfolioDashboard from './PortfolioDashboard';
import AdvancedOrders from './AdvancedOrders';
import OptionsTrading from './OptionsTrading';
import PerpetualFutures from './PerpetualFutures';
import MarketMaker from './MarketMaker';

const TradingHub = () => {
  const [activeTab, setActiveTab] = useState('spot');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4 md:p-6">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-7xl mx-auto"
      >
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent">
              Trading Hub
            </h1>
            <p className="text-slate-400 mt-1">
              All trading functions in one place
            </p>
          </div>
          <Badge variant="outline" className="text-green-400 border-green-400/50">
            <Wallet className="w-3 h-3 mr-1" />
            Kraken Connected
          </Badge>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="glass-card flex-wrap h-auto p-1 gap-1">
            <TabsTrigger value="spot" className="data-[state=active]:bg-green-500/20">
              <Wallet className="w-4 h-4 mr-2" />
              Spot
            </TabsTrigger>
            <TabsTrigger value="positions" className="data-[state=active]:bg-blue-500/20">
              <Briefcase className="w-4 h-4 mr-2" />
              Positions
            </TabsTrigger>
            <TabsTrigger value="portfolio" className="data-[state=active]:bg-purple-500/20">
              <PieChart className="w-4 h-4 mr-2" />
              Portfolio
            </TabsTrigger>
            <TabsTrigger value="advanced" className="data-[state=active]:bg-amber-500/20">
              <Layers className="w-4 h-4 mr-2" />
              Advanced
            </TabsTrigger>
            <TabsTrigger value="options" className="data-[state=active]:bg-cyan-500/20">
              <Target className="w-4 h-4 mr-2" />
              Options
            </TabsTrigger>
            <TabsTrigger value="perpetuals" className="data-[state=active]:bg-pink-500/20">
              <LineChart className="w-4 h-4 mr-2" />
              Perpetuals
            </TabsTrigger>
            <TabsTrigger value="market-maker" className="data-[state=active]:bg-orange-500/20">
              <Activity className="w-4 h-4 mr-2" />
              Market Maker
            </TabsTrigger>
          </TabsList>

          <TabsContent value="spot" className="mt-0">
            <SpotTrading embedded={true} />
          </TabsContent>

          <TabsContent value="positions" className="mt-0">
            <PositionManagement embedded={true} />
          </TabsContent>

          <TabsContent value="portfolio" className="mt-0">
            <PortfolioDashboard embedded={true} />
          </TabsContent>

          <TabsContent value="advanced" className="mt-0">
            <AdvancedOrders embedded={true} />
          </TabsContent>

          <TabsContent value="options" className="mt-0">
            <OptionsTrading embedded={true} />
          </TabsContent>

          <TabsContent value="perpetuals" className="mt-0">
            <PerpetualFutures embedded={true} />
          </TabsContent>

          <TabsContent value="market-maker" className="mt-0">
            <MarketMaker embedded={true} />
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default TradingHub;
