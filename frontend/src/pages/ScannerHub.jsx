import React, { lazy, memo } from 'react';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion } from 'framer-motion';
import { 
  Gem, Radar, Cpu, Users
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
const GemScanner = lazy(() => import('./GemScanner'));
const GemMLDLComparison = lazy(() => import('./GemMLDLComparison'));
const CopyTrading = lazy(() => import('./CopyTrading'));

const TABS = ['scanner', 'ml-dl', 'copy'];

const TAB_LABELS = {
  'scanner': 'Gem Scanner',
  'ml-dl': 'ML vs DL',
  'copy': 'Copy Trading'
};

const TAB_CONFIG = [
  { value: 'scanner', icon: Radar, label: 'Gem Scanner', color: 'pink' },
  { value: 'ml-dl', icon: Cpu, label: 'ML vs DL', color: 'purple' },
  { value: 'copy', icon: Users, label: 'Copy Trading', color: 'blue' },
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

const ScannerHub = () => {
  // URL-persisted tab state
  const [activeTab, setActiveTab] = useTabState(TABS, 'scanner');
  
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
          { label: 'Scanner & Social', href: '/scanner' },
          { label: TAB_LABELS[activeTab] }
        ]} />

        <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-pink-400 to-rose-400 bg-clip-text text-transparent">
              Scanner & Social
            </h1>
            <p className="text-slate-400 mt-1 text-sm md:text-base">
              Find gems and copy top traders
            </p>
          </div>
          <div className="flex items-center gap-3">
            <KeyboardHint />
            <Badge variant="outline" className="text-pink-400 border-pink-400/50">
              <Gem className="w-3 h-3 mr-1" />
              Scanning
            </Badge>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <MobileTabsList>
            <TabsList className="glass-card flex-nowrap md:flex-wrap h-auto p-1 gap-1 w-max md:w-auto">
              <TabsTrigger value="scanner" className="data-[state=active]:bg-pink-500/20 whitespace-nowrap">
                <Radar className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">Gem Scanner</span>
                <span className="sm:hidden">1</span>
              </TabsTrigger>
              <TabsTrigger value="ml-dl" className="data-[state=active]:bg-purple-500/20 whitespace-nowrap">
                <Cpu className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">ML vs DL</span>
                <span className="sm:hidden">2</span>
              </TabsTrigger>
              <TabsTrigger value="copy" className="data-[state=active]:bg-blue-500/20 whitespace-nowrap">
                <Users className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">Copy Trading</span>
                <span className="sm:hidden">3</span>
              </TabsTrigger>
            </TabsList>
          </MobileTabsList>

          <TabsContent value="scanner" className="mt-0">
            <GemScanner embedded={true} />
          </TabsContent>

          <TabsContent value="ml-dl" className="mt-0">
            <GemMLDLComparison embedded={true} />
          </TabsContent>

          <TabsContent value="copy" className="mt-0">
            <CopyTrading embedded={true} />
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default ScannerHub;
