import React, { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion } from 'framer-motion';
import { 
  Newspaper, Target, Calendar, Award, MessageSquare
} from 'lucide-react';

// Import existing page components
import NewsSentiment from './NewsSentiment';
import NewsAndIntelligence from './NewsAndIntelligence';
import EventTriggers from './EventTriggers';
import EventTimeline from './EventTimeline';
import TriggerPerformance from './TriggerPerformance';

const NewsHub = () => {
  const [activeTab, setActiveTab] = useState('sentiment');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4 md:p-6">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-7xl mx-auto"
      >
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent">
              News & Events
            </h1>
            <p className="text-slate-400 mt-1">
              Market news, sentiment analysis, and event triggers
            </p>
          </div>
          <Badge variant="outline" className="text-amber-400 border-amber-400/50">
            <Newspaper className="w-3 h-3 mr-1" />
            Live Feed
          </Badge>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="glass-card flex-wrap h-auto p-1 gap-1">
            <TabsTrigger value="sentiment" className="data-[state=active]:bg-amber-500/20">
              <MessageSquare className="w-4 h-4 mr-2" />
              Sentiment
            </TabsTrigger>
            <TabsTrigger value="intel" className="data-[state=active]:bg-blue-500/20">
              <Newspaper className="w-4 h-4 mr-2" />
              Intelligence
            </TabsTrigger>
            <TabsTrigger value="triggers" className="data-[state=active]:bg-red-500/20">
              <Target className="w-4 h-4 mr-2" />
              Triggers
            </TabsTrigger>
            <TabsTrigger value="timeline" className="data-[state=active]:bg-purple-500/20">
              <Calendar className="w-4 h-4 mr-2" />
              Timeline
            </TabsTrigger>
            <TabsTrigger value="performance" className="data-[state=active]:bg-green-500/20">
              <Award className="w-4 h-4 mr-2" />
              Stats
            </TabsTrigger>
          </TabsList>

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
