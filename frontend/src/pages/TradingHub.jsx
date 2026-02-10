import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion } from 'framer-motion';
import { 
  Wallet, Briefcase, PieChart, Layers, Target, LineChart, Activity,
  RefreshCw, TrendingUp, TrendingDown, DollarSign, ArrowUpRight, ArrowDownRight
} from 'lucide-react';
import { Breadcrumb, useTabKeyboardNav, KeyboardHint, MobileTabsList } from '@/components/HubNavigation';

// Import existing page components as sub-components
import SpotTrading from './SpotTrading';
import PositionManagement from './PositionManagement';
import PortfolioDashboard from './PortfolioDashboard';
import AdvancedOrders from './AdvancedOrders';
import OptionsTrading from './OptionsTrading';
import PerpetualFutures from './PerpetualFutures';
import MarketMaker from './MarketMaker';

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

const TradingHub = () => {
  const [activeTab, setActiveTab] = useState('spot');
  
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
              <TabsTrigger value="spot" className="data-[state=active]:bg-green-500/20 whitespace-nowrap">
                <Wallet className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden xs:inline">Spot</span>
                <span className="xs:hidden">1</span>
              </TabsTrigger>
              <TabsTrigger value="positions" className="data-[state=active]:bg-blue-500/20 whitespace-nowrap">
                <Briefcase className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden xs:inline">Positions</span>
                <span className="xs:hidden">2</span>
              </TabsTrigger>
              <TabsTrigger value="portfolio" className="data-[state=active]:bg-purple-500/20 whitespace-nowrap">
                <PieChart className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden xs:inline">Portfolio</span>
                <span className="xs:hidden">3</span>
              </TabsTrigger>
              <TabsTrigger value="advanced" className="data-[state=active]:bg-amber-500/20 whitespace-nowrap">
                <Layers className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden xs:inline">Advanced</span>
                <span className="xs:hidden">4</span>
              </TabsTrigger>
              <TabsTrigger value="options" className="data-[state=active]:bg-cyan-500/20 whitespace-nowrap">
                <Target className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden xs:inline">Options</span>
                <span className="xs:hidden">5</span>
              </TabsTrigger>
              <TabsTrigger value="perpetuals" className="data-[state=active]:bg-pink-500/20 whitespace-nowrap">
                <LineChart className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden xs:inline">Perpetuals</span>
                <span className="xs:hidden">6</span>
              </TabsTrigger>
              <TabsTrigger value="market-maker" className="data-[state=active]:bg-orange-500/20 whitespace-nowrap">
                <Activity className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden xs:inline">Market Maker</span>
                <span className="xs:hidden">7</span>
              </TabsTrigger>
            </TabsList>
          </MobileTabsList>

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
