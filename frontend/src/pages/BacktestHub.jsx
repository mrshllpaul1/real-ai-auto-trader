import React, { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion } from 'framer-motion';
import { 
  BarChart3, Calendar, Gem, LineChart, Shield
} from 'lucide-react';
import { Breadcrumb, useTabKeyboardNav, KeyboardHint, MobileTabsList } from '@/components/HubNavigation';

// Import existing page components
import BacktestEngine from './BacktestEngine';
import YearlyBacktest from './YearlyBacktest';
import GemBacktester from './GemBacktester';
import Analytics from './Analytics';
import RiskAnalyzer from './RiskAnalyzer';

const TABS = ['engine', 'yearly', 'gems', 'analytics', 'risk'];

const TAB_LABELS = {
  'engine': 'Backtest',
  'yearly': 'Yearly',
  'gems': 'Gems',
  'analytics': 'Analytics',
  'risk': 'Risk'
};

const BacktestHub = () => {
  const [activeTab, setActiveTab] = useState('engine');
  
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
          { label: 'Backtest & Analysis', href: '/backtest' },
          { label: TAB_LABELS[activeTab] }
        ]} />

        <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
              Backtest & Analysis
            </h1>
            <p className="text-slate-400 mt-1 text-sm md:text-base">
              Test strategies and analyze performance
            </p>
          </div>
          <div className="flex items-center gap-3">
            <KeyboardHint />
            <Badge variant="outline" className="text-blue-400 border-blue-400/50">
              <BarChart3 className="w-3 h-3 mr-1" />
              2020-2026 Data
            </Badge>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <MobileTabsList>
            <TabsList className="glass-card flex-nowrap md:flex-wrap h-auto p-1 gap-1 w-max md:w-auto">
              <TabsTrigger value="engine" className="data-[state=active]:bg-blue-500/20 whitespace-nowrap">
                <BarChart3 className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">Backtest</span>
                <span className="sm:hidden">1</span>
              </TabsTrigger>
              <TabsTrigger value="yearly" className="data-[state=active]:bg-purple-500/20 whitespace-nowrap">
                <Calendar className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">Yearly</span>
                <span className="sm:hidden">2</span>
              </TabsTrigger>
              <TabsTrigger value="gems" className="data-[state=active]:bg-amber-500/20 whitespace-nowrap">
                <Gem className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">Gems</span>
                <span className="sm:hidden">3</span>
              </TabsTrigger>
              <TabsTrigger value="analytics" className="data-[state=active]:bg-green-500/20 whitespace-nowrap">
                <LineChart className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">Analytics</span>
                <span className="sm:hidden">4</span>
              </TabsTrigger>
              <TabsTrigger value="risk" className="data-[state=active]:bg-red-500/20 whitespace-nowrap">
                <Shield className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">Risk</span>
                <span className="sm:hidden">5</span>
              </TabsTrigger>
            </TabsList>
          </MobileTabsList>

          <TabsContent value="engine" className="mt-0">
            <BacktestEngine embedded={true} />
          </TabsContent>

          <TabsContent value="yearly" className="mt-0">
            <YearlyBacktest embedded={true} />
          </TabsContent>

          <TabsContent value="gems" className="mt-0">
            <GemBacktester embedded={true} />
          </TabsContent>

          <TabsContent value="analytics" className="mt-0">
            <Analytics embedded={true} />
          </TabsContent>

          <TabsContent value="risk" className="mt-0">
            <RiskAnalyzer embedded={true} />
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default BacktestHub;
