import React, { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion } from 'framer-motion';
import { 
  Settings as SettingsIcon, Key, Shield, MessageCircle, BookOpen, Layout
} from 'lucide-react';

// Import existing page components
import Settings from './Settings';
import Setup from './Setup';
import TradingBudget from './TradingBudget';
import TelegramNotifications from './TelegramNotifications';
import TradingJournal from './TradingJournal';
import Guide from './Guide';
import DashboardCustomization from './DashboardCustomization';

const SettingsHub = () => {
  const [activeTab, setActiveTab] = useState('settings');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4 md:p-6">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-7xl mx-auto"
      >
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-400 to-zinc-400 bg-clip-text text-transparent">
              Settings & Config
            </h1>
            <p className="text-slate-400 mt-1">
              Configure your trading environment
            </p>
          </div>
          <Badge variant="outline" className="text-slate-400 border-slate-400/50">
            <SettingsIcon className="w-3 h-3 mr-1" />
            Configuration
          </Badge>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="glass-card flex-wrap h-auto p-1 gap-1">
            <TabsTrigger value="settings" className="data-[state=active]:bg-slate-500/20">
              <SettingsIcon className="w-4 h-4 mr-2" />
              Settings
            </TabsTrigger>
            <TabsTrigger value="setup" className="data-[state=active]:bg-amber-500/20">
              <Key className="w-4 h-4 mr-2" />
              API Setup
            </TabsTrigger>
            <TabsTrigger value="budget" className="data-[state=active]:bg-green-500/20">
              <Shield className="w-4 h-4 mr-2" />
              Budget
            </TabsTrigger>
            <TabsTrigger value="telegram" className="data-[state=active]:bg-blue-500/20">
              <MessageCircle className="w-4 h-4 mr-2" />
              Telegram
            </TabsTrigger>
            <TabsTrigger value="journal" className="data-[state=active]:bg-purple-500/20">
              <BookOpen className="w-4 h-4 mr-2" />
              Journal
            </TabsTrigger>
            <TabsTrigger value="guide" className="data-[state=active]:bg-cyan-500/20">
              <BookOpen className="w-4 h-4 mr-2" />
              Guide
            </TabsTrigger>
            <TabsTrigger value="customize" className="data-[state=active]:bg-pink-500/20">
              <Layout className="w-4 h-4 mr-2" />
              Customize
            </TabsTrigger>
          </TabsList>

          <TabsContent value="settings" className="mt-0">
            <Settings embedded={true} />
          </TabsContent>

          <TabsContent value="setup" className="mt-0">
            <Setup embedded={true} />
          </TabsContent>

          <TabsContent value="budget" className="mt-0">
            <TradingBudget embedded={true} />
          </TabsContent>

          <TabsContent value="telegram" className="mt-0">
            <TelegramNotifications embedded={true} />
          </TabsContent>

          <TabsContent value="journal" className="mt-0">
            <TradingJournal embedded={true} />
          </TabsContent>

          <TabsContent value="guide" className="mt-0">
            <Guide embedded={true} />
          </TabsContent>

          <TabsContent value="customize" className="mt-0">
            <DashboardCustomization embedded={true} />
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default SettingsHub;
