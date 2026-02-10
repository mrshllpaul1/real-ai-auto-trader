import React, { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion } from 'framer-motion';
import { 
  Brain, Zap, Bot, Layers, Wand2, GraduationCap, Cpu, Activity, Gauge, Sparkles
} from 'lucide-react';
import { Breadcrumb, useTabKeyboardNav, KeyboardHint, MobileTabsList } from '@/components/HubNavigation';

// Import existing page components
import AICommandCenter from './AICommandCenter';
import AdaptiveStrategy from './AdaptiveStrategy';
import AutoTrading from './AutoTrading';
import AutoExecution from './AutoExecution';
import EnsembleAI from './EnsembleAI';
import StrategyBuilder from './StrategyBuilder';
import AILearning from './AILearning';
import AITeacher from './AITeacher';
import AILearningLoop from './AILearningLoop';
import ModelPerformanceDashboard from './ModelPerformanceDashboard';
import EnhancedMTFPredictions from './EnhancedMTFPredictions';

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

const AIHub = () => {
  const [activeTab, setActiveTab] = useState('center');
  
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
              <TabsTrigger value="center" className="data-[state=active]:bg-purple-500/20 whitespace-nowrap">
                <Brain className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">AI Center</span>
                <span className="sm:hidden">1</span>
              </TabsTrigger>
              <TabsTrigger value="adaptive" className="data-[state=active]:bg-cyan-500/20 whitespace-nowrap">
                <Gauge className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">Adaptive</span>
                <span className="sm:hidden">2</span>
              </TabsTrigger>
              <TabsTrigger value="auto" className="data-[state=active]:bg-green-500/20 whitespace-nowrap">
                <Zap className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">Auto</span>
                <span className="sm:hidden">3</span>
              </TabsTrigger>
              <TabsTrigger value="execute" className="data-[state=active]:bg-amber-500/20 whitespace-nowrap">
                <Bot className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">Execute</span>
                <span className="sm:hidden">4</span>
              </TabsTrigger>
              <TabsTrigger value="ensemble" className="data-[state=active]:bg-pink-500/20 whitespace-nowrap">
                <Layers className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">Ensemble</span>
                <span className="sm:hidden">5</span>
              </TabsTrigger>
              <TabsTrigger value="builder" className="data-[state=active]:bg-blue-500/20 whitespace-nowrap">
                <Wand2 className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">Builder</span>
                <span className="sm:hidden">6</span>
              </TabsTrigger>
              <TabsTrigger value="learning" className="data-[state=active]:bg-indigo-500/20 whitespace-nowrap">
                <GraduationCap className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">Learning</span>
                <span className="sm:hidden">7</span>
              </TabsTrigger>
              <TabsTrigger value="models" className="data-[state=active]:bg-orange-500/20 whitespace-nowrap">
                <Cpu className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">Models</span>
                <span className="sm:hidden">8</span>
              </TabsTrigger>
              <TabsTrigger value="predictions" className="data-[state=active]:bg-red-500/20 whitespace-nowrap">
                <Activity className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">MTF</span>
                <span className="sm:hidden">9</span>
              </TabsTrigger>
            </TabsList>
          </MobileTabsList>

          <TabsContent value="center" className="mt-0">
            <AICommandCenter embedded={true} />
          </TabsContent>

          <TabsContent value="adaptive" className="mt-0">
            <AdaptiveStrategy embedded={true} />
          </TabsContent>

          <TabsContent value="auto" className="mt-0">
            <AutoTrading embedded={true} />
          </TabsContent>

          <TabsContent value="execute" className="mt-0">
            <AutoExecution embedded={true} />
          </TabsContent>

          <TabsContent value="ensemble" className="mt-0">
            <EnsembleAI embedded={true} />
          </TabsContent>

          <TabsContent value="builder" className="mt-0">
            <StrategyBuilder embedded={true} />
          </TabsContent>

          <TabsContent value="learning" className="mt-0">
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
          </TabsContent>

          <TabsContent value="models" className="mt-0">
            <ModelPerformanceDashboard embedded={true} />
          </TabsContent>

          <TabsContent value="predictions" className="mt-0">
            <EnhancedMTFPredictions embedded={true} />
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default AIHub;
