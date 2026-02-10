import React, { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion } from 'framer-motion';
import { 
  Newspaper, Target, Calendar, Award, MessageSquare
} from 'lucide-react';
import { Breadcrumb, useTabKeyboardNav, KeyboardHint, MobileTabsList } from '@/components/HubNavigation';

// Import existing page components
import NewsSentiment from './NewsSentiment';
import NewsAndIntelligence from './NewsAndIntelligence';
import EventTriggers from './EventTriggers';
import EventTimeline from './EventTimeline';
import TriggerPerformance from './TriggerPerformance';

const TABS = ['sentiment', 'intel', 'triggers', 'timeline', 'performance'];

const TAB_LABELS = {
  'sentiment': 'Sentiment',
  'intel': 'Intelligence',
  'triggers': 'Triggers',
  'timeline': 'Timeline',
  'performance': 'Stats'
};

const NewsHub = () => {
  const [activeTab, setActiveTab] = useState('sentiment');
  
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
          { label: 'News & Events', href: '/news' },
          { label: TAB_LABELS[activeTab] }
        ]} />

        <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent">
              News & Events
            </h1>
            <p className="text-slate-400 mt-1 text-sm md:text-base">
              Market news, sentiment analysis, and event triggers
            </p>
          </div>
          <div className="flex items-center gap-3">
            <KeyboardHint />
            <Badge variant="outline" className="text-amber-400 border-amber-400/50">
              <Newspaper className="w-3 h-3 mr-1" />
              Live Feed
            </Badge>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <MobileTabsList>
            <TabsList className="glass-card flex-nowrap md:flex-wrap h-auto p-1 gap-1 w-max md:w-auto">
              <TabsTrigger value="sentiment" className="data-[state=active]:bg-amber-500/20 whitespace-nowrap">
                <MessageSquare className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">Sentiment</span>
                <span className="sm:hidden">1</span>
              </TabsTrigger>
              <TabsTrigger value="intel" className="data-[state=active]:bg-blue-500/20 whitespace-nowrap">
                <Newspaper className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">Intelligence</span>
                <span className="sm:hidden">2</span>
              </TabsTrigger>
              <TabsTrigger value="triggers" className="data-[state=active]:bg-red-500/20 whitespace-nowrap">
                <Target className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">Triggers</span>
                <span className="sm:hidden">3</span>
              </TabsTrigger>
              <TabsTrigger value="timeline" className="data-[state=active]:bg-purple-500/20 whitespace-nowrap">
                <Calendar className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">Timeline</span>
                <span className="sm:hidden">4</span>
              </TabsTrigger>
              <TabsTrigger value="performance" className="data-[state=active]:bg-green-500/20 whitespace-nowrap">
                <Award className="w-4 h-4 mr-1 md:mr-2" />
                <span className="hidden sm:inline">Stats</span>
                <span className="sm:hidden">5</span>
              </TabsTrigger>
            </TabsList>
          </MobileTabsList>

          <TabsContent value="sentiment" className="mt-0">
            <NewsSentiment embedded={true} />
          </TabsContent>

          <TabsContent value="intel" className="mt-0">
            <NewsAndIntelligence embedded={true} />
          </TabsContent>

          <TabsContent value="triggers" className="mt-0">
            <EventTriggers embedded={true} />
          </TabsContent>

          <TabsContent value="timeline" className="mt-0">
            <EventTimeline embedded={true} />
          </TabsContent>

          <TabsContent value="performance" className="mt-0">
            <TriggerPerformance embedded={true} />
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default NewsHub;
