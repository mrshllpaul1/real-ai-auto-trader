// AIHub - AI Features Center - Updated Feb 2026
import React, { lazy, memo, Suspense } from 'react';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion } from 'framer-motion';
import { 
  Brain, Zap, Bot, Layers, Wand2, GraduationCap, Cpu, Activity, Gauge
} from 'lucide-react';
import { 
  Breadcrumb, 
  useTabState, 
  useTabKeyboardNav, 
  KeyboardHint, 
  MobileTabsList,
  LazyTabContent 
} from '@/components/HubNavigation';

// Import visual training progress component directly for quick loading
import VisualTrainingProgress from '@/components/VisualTrainingProgress';

// Lazy load page components
const AICommandCenter = lazy(() => import('./AICommandCenter'));
const AdaptiveStrategy = lazy(() => import('./AdaptiveStrategy'));
const AutoTrading = lazy(() => import('./AutoTrading'));
const AutoExecution = lazy(() => import('./AutoExecution'));
const EnsembleAI = lazy(() => import('./EnsembleAI'));
const StrategyBuilder = lazy(() => import('./StrategyBuilder'));
const AILearning = lazy(() => import('./AILearning'));
const AITeacher = lazy(() => import('./AITeacher'));
const AILearningLoop = lazy(() => import('./AILearningLoop'));
const ModelPerformanceDashboard = lazy(() => import('./ModelPerformanceDashboard'));
const EnhancedMTFPredictions = lazy(() => import('./EnhancedMTFPredictions'));

const TABS = ['center', 'adaptive', 'auto', 'execute', 'ensemble', 'builder', 'learning', 'models', 'predictions'];

const TAB_LABELS = {
  'center': 'AI Center',
  'adaptive': 'Adaptive',
  'auto': 'Auto Trade',
  'execute': 'Execute',
  'ensemble': 'Ensemble',
  'builder': 'Builder',
  'learning': 'Learning',
  'models': 'Models',
  'predictions': 'MTF'
};

const TAB_CONFIG = [
  { value: 'center', icon: Brain, label: 'AI Center', color: 'purple' },
  { value: 'adaptive', icon: Gauge, label: 'Adaptive', color: 'cyan' },
  { value: 'auto', icon: Zap, label: 'Auto', color: 'green' },
  { value: 'execute', icon: Bot, label: 'Execute', color: 'amber' },
  { value: 'ensemble', icon: Layers, label: 'Ensemble', color: 'pink' },
  { value: 'builder', icon: Wand2, label: 'Builder', color: 'blue' },
  { value: 'learning', icon: GraduationCap, label: 'Learning', color: 'indigo' },
  { value: 'models', icon: Cpu, label: 'Models', color: 'orange' },
  { value: 'predictions', icon: Activity, label: 'MTF', color: 'red' },
];

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

const AIHub = () => {
  const [activeTab, setActiveTab] = useTabState(TABS, 'center');
  useTabKeyboardNav(TABS, activeTab, setActiveTab);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4 md:p-6">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-7xl mx-auto"
      >
        <Breadcrumb items={[
          { label: 'AI & Strategy', href: '/ai' },
          { label: TAB_LABELS[activeTab] }
        ]} />

        <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              AI & Strategy Hub
            </h1>
            <p className="text-slate-400 mt-1 text-sm md:text-base">
              AI-powered trading intelligence and automation
            </p>
          </div>
          <div className="flex items-center gap-3">
            <KeyboardHint />
            <Badge variant="outline" className="text-purple-400 border-purple-400/50">
              <Brain className="w-3 h-3 mr-1" />
              AI Active
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

          <TabsContent value="center" className="mt-0">
            <LazyTabContent isActive={activeTab === 'center'}>
              <AICommandCenter embedded={true} />
            </LazyTabContent>
          </TabsContent>

          <TabsContent value="adaptive" className="mt-0">
            <LazyTabContent isActive={activeTab === 'adaptive'}>
              <AdaptiveStrategy embedded={true} />
            </LazyTabContent>
          </TabsContent>

          <TabsContent value="auto" className="mt-0">
            <LazyTabContent isActive={activeTab === 'auto'}>
              <AutoTrading embedded={true} />
            </LazyTabContent>
          </TabsContent>

          <TabsContent value="execute" className="mt-0">
            <LazyTabContent isActive={activeTab === 'execute'}>
              <AutoExecution embedded={true} />
            </LazyTabContent>
          </TabsContent>

          <TabsContent value="ensemble" className="mt-0">
            <LazyTabContent isActive={activeTab === 'ensemble'}>
              <EnsembleAI embedded={true} />
            </LazyTabContent>
          </TabsContent>

          <TabsContent value="builder" className="mt-0">
            <LazyTabContent isActive={activeTab === 'builder'}>
              <StrategyBuilder embedded={true} />
            </LazyTabContent>
          </TabsContent>

          <TabsContent value="learning" className="mt-0">
            <LazyTabContent isActive={activeTab === 'learning'}>
              <div className="space-y-6">
                <Tabs defaultValue="ai-learning">
                  <TabsList className="mb-4">
                    <TabsTrigger value="ai-learning">AI Learning</TabsTrigger>
                    <TabsTrigger value="teacher">AI Teacher</TabsTrigger>
                    <TabsTrigger value="loop">Learning Loop</TabsTrigger>
                  </TabsList>
                  <TabsContent value="ai-learning">
                    <AILearning embedded={true} />
                  </TabsContent>
                  <TabsContent value="teacher">
                    <AITeacher embedded={true} />
                  </TabsContent>
                  <TabsContent value="loop">
                    <AILearningLoop embedded={true} />
                  </TabsContent>
                </Tabs>
              </div>
            </LazyTabContent>
          </TabsContent>

          <TabsContent value="models" className="mt-0">
            <LazyTabContent isActive={activeTab === 'models'}>
              <ModelPerformanceDashboard embedded={true} />
            </LazyTabContent>
          </TabsContent>

          <TabsContent value="predictions" className="mt-0">
            <LazyTabContent isActive={activeTab === 'predictions'}>
              <EnhancedMTFPredictions embedded={true} />
            </LazyTabContent>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default AIHub;
