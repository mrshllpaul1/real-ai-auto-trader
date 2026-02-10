import React, { lazy, memo } from 'react';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion } from 'framer-motion';
import { 
  Newspaper, Target, Calendar, Award, MessageSquare
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
const NewsSentiment = lazy(() => import('./NewsSentiment'));
const NewsAndIntelligence = lazy(() => import('./NewsAndIntelligence'));
const EventTriggers = lazy(() => import('./EventTriggers'));
const EventTimeline = lazy(() => import('./EventTimeline'));
const TriggerPerformance = lazy(() => import('./TriggerPerformance'));

const TABS = ['sentiment', 'intel', 'triggers', 'timeline', 'performance'];

const TAB_LABELS = {
  'sentiment': 'Sentiment',
  'intel': 'Intelligence',
  'triggers': 'Triggers',
  'timeline': 'Timeline',
  'performance': 'Stats'
};

const TAB_CONFIG = [
  { value: 'sentiment', icon: MessageSquare, label: 'Sentiment', color: 'amber' },
  { value: 'intel', icon: Newspaper, label: 'Intelligence', color: 'blue' },
  { value: 'triggers', icon: Target, label: 'Triggers', color: 'red' },
  { value: 'timeline', icon: Calendar, label: 'Timeline', color: 'purple' },
  { value: 'performance', icon: Award, label: 'Stats', color: 'green' },
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

const NewsHub = () => {
  // URL-persisted tab state
  const [activeTab, setActiveTab] = useTabState(TABS, 'sentiment');
  
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
              {TAB_CONFIG.map((tab) => (
                <TabTriggerItem key={tab.value} {...tab} />
              ))}
            </TabsList>
          </MobileTabsList>

          {/* Lazy-loaded tab content - only renders active tab */}
          <TabsContent value="sentiment" className="mt-0">
            <LazyTabContent isActive={activeTab === 'sentiment'}>
              <NewsSentiment embedded={true} />
            </LazyTabContent>
          </TabsContent>

          <TabsContent value="intel" className="mt-0">
            <LazyTabContent isActive={activeTab === 'intel'}>
              <NewsAndIntelligence embedded={true} />
            </LazyTabContent>
          </TabsContent>

          <TabsContent value="triggers" className="mt-0">
            <LazyTabContent isActive={activeTab === 'triggers'}>
              <EventTriggers embedded={true} />
            </LazyTabContent>
          </TabsContent>

          <TabsContent value="timeline" className="mt-0">
            <LazyTabContent isActive={activeTab === 'timeline'}>
              <EventTimeline embedded={true} />
            </LazyTabContent>
          </TabsContent>

          <TabsContent value="performance" className="mt-0">
            <LazyTabContent isActive={activeTab === 'performance'}>
              <TriggerPerformance embedded={true} />
            </LazyTabContent>
          </TabsContent>
        </Tabs>
      </motion.div>
    </div>
  );
};

export default NewsHub;
