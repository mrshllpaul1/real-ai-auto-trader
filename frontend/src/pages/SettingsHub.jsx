import React, { lazy, memo } from 'react';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion } from 'framer-motion';
import { 
  Settings as SettingsIcon, Key, Shield, MessageCircle, BookOpen, Layout,
  Volume2, Mail, Share2
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
const Settings = lazy(() => import('./Settings'));
const Setup = lazy(() => import('./Setup'));
const TradingBudget = lazy(() => import('./TradingBudget'));
const TelegramNotifications = lazy(() => import('./TelegramNotifications'));
const TradingJournal = lazy(() => import('./TradingJournal'));
const Guide = lazy(() => import('./Guide'));
const DashboardCustomization = lazy(() => import('./DashboardCustomization'));
const SoundSettings = lazy(() => import('./SoundSettings'));
const EmailDigest = lazy(() => import('./EmailDigest'));
const PortfolioShare = lazy(() => import('./PortfolioShare'));

const TABS = ['settings', 'setup', 'budget', 'telegram', 'journal', 'sounds', 'email', 'share', 'guide', 'customize'];

const TAB_LABELS = {
  'settings': 'Settings',
  'setup': 'API Setup',
  'budget': 'Budget',
  'telegram': 'Telegram',
  'journal': 'Journal',
  'sounds': 'Sound Alerts',
  'email': 'Email Digest',
  'share': 'Portfolio Share',
  'guide': 'Guide',
  'customize': 'Customize'
};

const TAB_CONFIG = [
  { value: 'settings', icon: SettingsIcon, label: 'Settings', color: 'slate' },
  { value: 'setup', icon: Key, label: 'API Setup', color: 'amber' },
  { value: 'budget', icon: Shield, label: 'Budget', color: 'green' },
  { value: 'telegram', icon: MessageCircle, label: 'Telegram', color: 'blue' },
  { value: 'journal', icon: BookOpen, label: 'Journal', color: 'purple' },
  { value: 'sounds', icon: Volume2, label: 'Sounds', color: 'emerald' },
  { value: 'email', icon: Mail, label: 'Email', color: 'orange' },
  { value: 'share', icon: Share2, label: 'Share', color: 'pink' },
  { value: 'guide', icon: BookOpen, label: 'Guide', color: 'cyan' },
  { value: 'customize', icon: Layout, label: 'Customize', color: 'rose' },
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

const SettingsHub = () => {
  // URL-persisted tab state
  const [activeTab, setActiveTab] = useTabState(TABS, 'settings');
  
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
              {TAB_CONFIG.map((tab) => (
                <TabTriggerItem key={tab.value} {...tab} />
              ))}
            </TabsList>
          </MobileTabsList>

          {/* Lazy-loaded tab content - only renders active tab */}
          <TabsContent value="settings" className="mt-0">
            <LazyTabContent isActive={activeTab === 'settings'}>
              <Settings embedded={true} />
            </LazyTabContent>
          </TabsContent>

          <TabsContent value="setup" className="mt-0">
            <LazyTabContent isActive={activeTab === 'setup'}>
              <Setup embedded={true} />
            </LazyTabContent>
          </TabsContent>

          <TabsContent value="budget" className="mt-0">
            <LazyTabContent isActive={activeTab === 'budget'}>
              <TradingBudget embedded={true} />
            </LazyTabContent>
          </TabsContent>

          <TabsContent value="telegram" className="mt-0">
            <LazyTabContent isActive={activeTab === 'telegram'}>
              <TelegramNotifications embedded={true} />
            </LazyTabContent>
          </TabsContent>

          <TabsContent value="journal" className="mt-0">
            <LazyTabContent isActive={activeTab === 'journal'}>
              <TradingJournal embedded={true} />
            </LazyTabContent>
          </TabsContent>

          <TabsContent value="guide" className="mt-0">
            <LazyTabContent isActive={activeTab === 'guide'}>
              <Guide embedded={true} />
            </LazyTabContent>
          </TabsContent>

          <TabsContent value="customize" className="mt-0">
            <LazyTabContent isActive={activeTab === 'customize'}>
              <DashboardCustomization embedded={true} />
            </LazyTabContent>
          </TabsContent>

          <TabsContent value="sounds" className="mt-0">
            <LazyTabContent isActive={activeTab === 'sounds'}>
              <SoundSettings embedded={true} />
            </LazyTabContent>
          </TabsContent>

          <TabsContent value="email" className="mt-0">
            <LazyTabContent isActive={activeTab === 'email'}>
              <EmailDigest embedded={true} />
            </LazyTabContent>
          </TabsContent>

          <TabsContent value="share" className="mt-0">
            <LazyTabContent isActive={activeTab === 'share'}>
              <PortfolioShare embedded={true} />
            </LazyTabContent>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default SettingsHub;
