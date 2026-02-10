import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion } from 'framer-motion';
import { 
  Brain, Zap, Bot, Layers, Wand2, GraduationCap, Cpu, Activity, Gauge, Sparkles
} from 'lucide-react';

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

const AIHub = () => {
  const [activeTab, setActiveTab] = useState('center');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4 md:p-6">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-7xl mx-auto"
      >
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              AI & Strategy Hub
            </h1>
            <p className="text-slate-400 mt-1">
              AI-powered trading intelligence and automation
            </p>
          </div>
          <Badge variant="outline" className="text-purple-400 border-purple-400/50">
            <Brain className="w-3 h-3 mr-1" />
            AI Active
          </Badge>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="glass-card flex-wrap h-auto p-1 gap-1">
            <TabsTrigger value="center" className="data-[state=active]:bg-purple-500/20">
              <Brain className="w-4 h-4 mr-2" />
              AI Center
            </TabsTrigger>
            <TabsTrigger value="adaptive" className="data-[state=active]:bg-cyan-500/20">
              <Gauge className="w-4 h-4 mr-2" />
              Adaptive
            </TabsTrigger>
            <TabsTrigger value="auto" className="data-[state=active]:bg-green-500/20">
              <Zap className="w-4 h-4 mr-2" />
              Auto Trade
            </TabsTrigger>
            <TabsTrigger value="execute" className="data-[state=active]:bg-amber-500/20">
              <Bot className="w-4 h-4 mr-2" />
              Execute
            </TabsTrigger>
            <TabsTrigger value="ensemble" className="data-[state=active]:bg-pink-500/20">
              <Layers className="w-4 h-4 mr-2" />
              Ensemble
            </TabsTrigger>
            <TabsTrigger value="builder" className="data-[state=active]:bg-blue-500/20">
              <Wand2 className="w-4 h-4 mr-2" />
              Builder
            </TabsTrigger>
            <TabsTrigger value="learning" className="data-[state=active]:bg-indigo-500/20">
              <GraduationCap className="w-4 h-4 mr-2" />
              Learning
            </TabsTrigger>
            <TabsTrigger value="models" className="data-[state=active]:bg-orange-500/20">
              <Cpu className="w-4 h-4 mr-2" />
              Models
            </TabsTrigger>
            <TabsTrigger value="predictions" className="data-[state=active]:bg-red-500/20">
              <Activity className="w-4 h-4 mr-2" />
              MTF
            </TabsTrigger>
          </TabsList>

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
