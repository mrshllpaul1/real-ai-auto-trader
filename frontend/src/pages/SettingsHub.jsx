import React, { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion } from 'framer-motion';
import { 
  Settings as SettingsIcon, Key, Shield, MessageCircle, BookOpen, Layout
} from 'lucide-react';
import { Breadcrumb, useTabKeyboardNav, KeyboardHint, MobileTabsList } from '@/components/HubNavigation';

// Import existing page components
import Settings from './Settings';
import Setup from './Setup';
import TradingBudget from './TradingBudget';
import TelegramNotifications from './TelegramNotifications';
import TradingJournal from './TradingJournal';
import Guide from './Guide';
import DashboardCustomization from './DashboardCustomization';

const TABS = ['settings', 'setup', 'budget', 'telegram', 'journal', 'guide', 'customize'];

const TAB_LABELS = {
  'settings': 'Settings',
  'setup': 'API Setup',
  'budget': 'Budget',
  'telegram': 'Telegram',
  'journal': 'Journal',
  'guide': 'Guide',
  'customize': 'Customize'
};

const SettingsHub = () => {
  const [activeTab, setActiveTab] = useState('settings');
  
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
          { label: 'Settings', href: '/settings' },
          { label: TAB_LABELS[activeTab] }
        ]} />

        <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-slate-400 to-zinc-400 bg-clip-text text-transparent">
              Settings & Config
            </h1>
            <p className="text-slate-400 mt-1 text-sm md:text-base">
              Configure your trading environment
            </p>
          </div>
          <div className="flex items-center gap-3">
            <KeyboardHint />
            <Badge variant="outline" className="text-slate-400 border-slate-400/50">
              <SettingsIcon className="w-3 h-3 mr-1" />
              Configuration
            </Badge>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <MobileTabsList>
            <TabsList className="glass-card flex-nowrap md:flex-wrap h-auto p-1 gap-1 w-max md:w-auto">
              <TabsTrigger value="settings" className="data-[state=active]:bg-slate-500/20 whitespace-nowrap">
                <SettingsIcon className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">Settings</span>
                <span className="sm:hidden">1</span>
              </TabsTrigger>
              <TabsTrigger value="setup" className="data-[state=active]:bg-amber-500/20 whitespace-nowrap">
                <Key className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">API Setup</span>
                <span className="sm:hidden">2</span>
              </TabsTrigger>
              <TabsTrigger value="budget" className="data-[state=active]:bg-green-500/20 whitespace-nowrap">
                <Shield className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">Budget</span>
                <span className="sm:hidden">3</span>
              </TabsTrigger>
              <TabsTrigger value="telegram" className="data-[state=active]:bg-blue-500/20 whitespace-nowrap">
                <MessageCircle className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">Telegram</span>
                <span className="sm:hidden">4</span>
              </TabsTrigger>
              <TabsTrigger value="journal" className="data-[state=active]:bg-purple-500/20 whitespace-nowrap">
                <BookOpen className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">Journal</span>
                <span className="sm:hidden">5</span>
              </TabsTrigger>
              <TabsTrigger value="guide" className="data-[state=active]:bg-cyan-500/20 whitespace-nowrap">
                <BookOpen className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">Guide</span>
                <span className="sm:hidden">6</span>
              </TabsTrigger>
              <TabsTrigger value="customize" className="data-[state=active]:bg-pink-500/20 whitespace-nowrap">
                <Layout className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">Customize</span>
                <span className="sm:hidden">7</span>
              </TabsTrigger>
            </TabsList>
          </MobileTabsList>

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
