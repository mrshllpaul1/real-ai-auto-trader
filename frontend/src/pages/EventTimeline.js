import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Calendar, TrendingUp, TrendingDown, AlertTriangle, Clock,
  Search, Filter, RefreshCw, ExternalLink, Newspaper,
  DollarSign, Building2, Shield, Users, Zap, Globe, Target,
  Activity, Eye, Bell, ChevronRight
} from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';

const EventTimeline = () => {
  const [events, setEvents] = useState([]);
  const [correlatedEvents, setCorrelatedEvents] = useState([]);
  const [upcomingEvents, setUpcomingEvents] = useState([]);
  const [patterns, setPatterns] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('timeline');
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [timeRange, setTimeRange] = useState('30');

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [eventsRes, correlatedRes, upcomingRes, patternsRes] = await Promise.all([
        api.get(`/events/database/list?limit=100`).catch(() => ({ data: { events: [] } })),
        api.get(`/events/database/search?keyword=price&limit=30`).catch(() => ({ data: { events: [] } })),
        api.get(`/events/patterns/upcoming`).catch(() => ({ data: { upcoming_events: [] } })),
        api.get(`/events/patterns/all`).catch(() => ({ data: null }))
      ]);

      setEvents(eventsRes.data?.events || []);
      setCorrelatedEvents(correlatedRes.data?.events || []);
      setUpcomingEvents(upcomingRes.data?.upcoming_events || []);
      setPatterns(patternsRes.data);
    } catch (error) {
      console.error('Error loading events:', error);
      toast.error('Failed to load events');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    try {
      setLoading(true);
      const response = await api.get(`/events/database/search?keyword=${encodeURIComponent(searchQuery)}&limit=50`);
      setEvents(response.data?.events || []);
      toast.success(`Found ${response.data?.events?.length || 0} events`);
    } catch (error) {
      toast.error('Search failed');
    } finally {
      setLoading(false);
    }
  };

  const getCategoryIcon = (category) => {
    const cat = (category || '').toLowerCase();
    if (cat.includes('regulat') || cat.includes('sec') || cat.includes('legal')) 
      return <Shield className="text-[#FF0055]" size={16} />;
    if (cat.includes('hack') || cat.includes('security') || cat.includes('exploit')) 
      return <AlertTriangle className="text-[#FF0055]" size={16} />;
    if (cat.includes('partnership') || cat.includes('institutional') || cat.includes('adoption')) 
      return <Building2 className="text-[#00FF94]" size={16} />;
    if (cat.includes('celebrity') || cat.includes('elon') || cat.includes('influencer')) 
      return <Users className="text-[#FFB800]" size={16} />;
    if (cat.includes('price') || cat.includes('market') || cat.includes('trading')) 
      return <DollarSign className="text-[#9D00FF]" size={16} />;
    if (cat.includes('tech') || cat.includes('upgrade') || cat.includes('launch')) 
      return <Zap className="text-[#007AFF]" size={16} />;
    return <Globe className="text-[#A1A1AA]" size={16} />;
  };

  const getSentimentColor = (sentiment) => {
    // Handle both numeric sentiment and string impact
    if (typeof sentiment === 'string') {
      if (sentiment === 'positive') return 'text-[#00FF94]';
      if (sentiment === 'negative') return 'text-[#FF0055]';
      return 'text-[#FFB800]';
    }
    if (sentiment > 0.3) return 'text-[#00FF94]';
    if (sentiment < -0.3) return 'text-[#FF0055]';
    return 'text-[#FFB800]';
  };

  const getSentimentBadge = (sentiment, impact) => {
    // Handle string impact from database events
    if (impact) {
      if (impact === 'positive') return { color: 'bg-[#00FF94]/20 text-[#00FF94]', label: 'Bullish' };
      if (impact === 'negative') return { color: 'bg-[#FF0055]/20 text-[#FF0055]', label: 'Bearish' };
      return { color: 'bg-[#FFB800]/20 text-[#FFB800]', label: 'Mixed' };
    }
    // Handle numeric sentiment
    if (sentiment > 0.3) return { color: 'bg-[#00FF94]/20 text-[#00FF94]', label: 'Bullish' };
    if (sentiment < -0.3) return { color: 'bg-[#FF0055]/20 text-[#FF0055]', label: 'Bearish' };
    return { color: 'bg-[#FFB800]/20 text-[#FFB800]', label: 'Neutral' };
  };

  const formatDate = (dateStr) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
      });
    } catch {
      return dateStr;
    }
  };

  const filteredEvents = events.filter(event => {
    if (categoryFilter !== 'all') {
      const cat = (event.category || event.categories?.[0] || '').toLowerCase();
      if (!cat.includes(categoryFilter.toLowerCase())) return false;
    }
    return true;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-[#9D00FF] mx-auto mb-4" />
          <p className="text-[#A1A1AA]">Loading Event Timeline...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 lg:p-8 space-y-6" data-testid="event-timeline-page">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex flex-col lg:flex-row lg:items-center justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl lg:text-4xl font-heading font-black tracking-tight mb-2 flex items-center gap-3">
            <Calendar size={40} className="text-[#007AFF]" />
            <span className="text-[#007AFF]">Event</span> Timeline
          </h1>
          <p className="text-[#A1A1AA]">
            Historical crypto events correlated with price movements
          </p>
        </div>
        <Button
          onClick={loadData}
          variant="outline"
          className="border-[#007AFF] text-[#007AFF] hover:bg-[#007AFF]/10"
          data-testid="refresh-btn"
        >
          <RefreshCw size={16} className="mr-2" />
          Refresh
        </Button>
      </motion.div>

      {/* Search & Filters */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="flex flex-col lg:flex-row gap-4"
      >
        <div className="flex-1 flex gap-2">
          <Input
            placeholder="Search events (e.g., 'FTX collapse', 'ETF approval')..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            className="bg-[#121212] border-[#1F1F1F]"
            data-testid="search-input"
          />
          <Button onClick={handleSearch} className="bg-[#007AFF]">
            <Search size={16} />
          </Button>
        </div>
        <Select value={categoryFilter} onValueChange={setCategoryFilter}>
          <SelectTrigger className="w-48 bg-[#121212] border-[#1F1F1F]">
            <Filter size={16} className="mr-2" />
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent className="bg-[#121212] border-[#1F1F1F]">
            <SelectItem value="all">All Categories</SelectItem>
            <SelectItem value="regulatory">Regulatory</SelectItem>
            <SelectItem value="hack">Hacks & Security</SelectItem>
            <SelectItem value="celebrity">Celebrity/Influencer</SelectItem>
            <SelectItem value="institutional">Institutional</SelectItem>
            <SelectItem value="tech">Technology</SelectItem>
            <SelectItem value="market">Market Events</SelectItem>
          </SelectContent>
        </Select>
      </motion.div>

      {/* Stats */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.15 }}
        className="grid grid-cols-2 lg:grid-cols-4 gap-4"
      >
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-3 mb-2">
              <Newspaper size={20} className="text-[#007AFF]" />
              <span className="text-sm text-[#A1A1AA]">Total Events</span>
            </div>
            <div className="text-3xl font-data font-bold text-white">
              {events.length}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-3 mb-2">
              <TrendingUp size={20} className="text-[#00FF94]" />
              <span className="text-sm text-[#A1A1AA]">Bullish Events</span>
            </div>
            <div className="text-3xl font-data font-bold text-[#00FF94]">
              {events.filter(e => e.impact === 'positive' || (e.sentiment || 0) > 0.3).length}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-3 mb-2">
              <TrendingDown size={20} className="text-[#FF0055]" />
              <span className="text-sm text-[#A1A1AA]">Bearish Events</span>
            </div>
            <div className="text-3xl font-data font-bold text-[#FF0055]">
              {events.filter(e => e.impact === 'negative' || (e.sentiment || 0) < -0.3).length}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-3 mb-2">
              <Zap size={20} className="text-[#9D00FF]" />
              <span className="text-sm text-[#A1A1AA]">Correlated</span>
            </div>
            <div className="text-3xl font-data font-bold text-[#9D00FF]">
              {correlatedEvents.length}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="bg-[#121212] border border-[#1F1F1F]">
          <TabsTrigger value="timeline" className="data-[state=active]:bg-[#007AFF]">
            Timeline ({filteredEvents.length})
          </TabsTrigger>
          <TabsTrigger value="correlated" className="data-[state=active]:bg-[#007AFF]">
            Price Impact ({correlatedEvents.length})
          </TabsTrigger>
          <TabsTrigger value="major" className="data-[state=active]:bg-[#007AFF]">
            Major Events
          </TabsTrigger>
        </TabsList>

        {/* Timeline Tab */}
        <TabsContent value="timeline" className="space-y-4">
          {filteredEvents.length === 0 ? (
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardContent className="py-12 text-center">
                <Calendar size={48} className="mx-auto mb-4 text-[#A1A1AA] opacity-50" />
                <p className="text-[#A1A1AA]">No events found</p>
              </CardContent>
            </Card>
          ) : (
            <div className="relative">
              {/* Timeline line */}
              <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-[#1F1F1F]" />
              
              <div className="space-y-4">
                {filteredEvents.map((event, index) => {
                  const sentimentBadge = getSentimentBadge(event.sentiment || 0, event.impact);
                  const isPositive = event.impact === 'positive' || (event.sentiment || 0) > 0.3;
                  const isNegative = event.impact === 'negative' || (event.sentiment || 0) < -0.3;
                  return (
                    <motion.div
                      key={event.event_id || index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.03 }}
                      className="relative pl-16"
                    >
                      {/* Timeline dot */}
                      <div className={`absolute left-4 w-5 h-5 rounded-full border-2 border-[#0A0A0A] flex items-center justify-center ${
                        isPositive ? 'bg-[#00FF94]' : 
                        isNegative ? 'bg-[#FF0055]' : 'bg-[#FFB800]'
                      }`}>
                        {getCategoryIcon(event.category || event.categories?.[0])}
                      </div>
                      
                      <Card className="bg-[#0A0A0A] border-[#1F1F1F] hover:border-[#007AFF]/50 transition-colors" data-testid={`event-${index}`}>
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                <span className="text-xs text-[#A1A1AA]">
                                  {formatDate(event.date || event.published_at)}
                                </span>
                                <Badge className={sentimentBadge.color}>
                                  {sentimentBadge.label}
                                </Badge>
                                {event.category && (
                                  <Badge variant="outline" className="text-xs border-[#1F1F1F]">
                                    {event.category}
                                  </Badge>
                                )}
                              </div>
                              <h3 className="font-bold text-white mb-2 line-clamp-2">
                                {event.event || event.title}
                              </h3>
                              {event.summary && (
                                <p className="text-sm text-[#A1A1AA] line-clamp-2">
                                  {event.summary}
                                </p>
                              )}
                              {(event.coins || event.coins_affected) && (event.coins || event.coins_affected).length > 0 && (
                                <div className="flex gap-1 mt-2">
                                  {(event.coins || event.coins_affected).slice(0, 5).map((coin, i) => (
                                    <Badge key={i} className="bg-[#9D00FF]/20 text-[#9D00FF] text-xs">
                                      {coin}
                                    </Badge>
                                  ))}
                                </div>
                              )}
                            </div>
                            {event.url && (
                              <a 
                                href={event.url} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="text-[#007AFF] hover:text-[#007AFF]/80"
                              >
                                <ExternalLink size={16} />
                              </a>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    </motion.div>
                  );
                })}
              </div>
            </div>
          )}
        </TabsContent>

        {/* Correlated Events Tab */}
        <TabsContent value="correlated" className="space-y-4">
          {correlatedEvents.length === 0 ? (
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardContent className="py-12 text-center">
                <TrendingUp size={48} className="mx-auto mb-4 text-[#A1A1AA] opacity-50" />
                <p className="text-[#A1A1AA]">No correlated events found</p>
                <p className="text-xs text-[#A1A1AA] mt-2">
                  Run the event correlation engine to link news with price movements
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {correlatedEvents.map((event, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid={`correlated-${index}`}>
                    <CardContent className="p-4">
                      <div className="flex items-start gap-4">
                        <div className={`p-3 rounded-lg ${
                          (event.price_change || 0) > 0 ? 'bg-[#00FF94]/20' : 'bg-[#FF0055]/20'
                        }`}>
                          {(event.price_change || 0) > 0 ? (
                            <TrendingUp className="text-[#00FF94]" />
                          ) : (
                            <TrendingDown className="text-[#FF0055]" />
                          )}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-xs text-[#A1A1AA]">
                              {formatDate(event.date)}
                            </span>
                            <Badge className={
                              (event.price_change || 0) > 0 
                                ? 'bg-[#00FF94]/20 text-[#00FF94]' 
                                : 'bg-[#FF0055]/20 text-[#FF0055]'
                            }>
                              {(event.price_change || 0) > 0 ? '+' : ''}{(event.price_change || 0).toFixed(1)}%
                            </Badge>
                            {event.coin && (
                              <Badge className="bg-[#9D00FF]/20 text-[#9D00FF]">
                                {event.coin}
                              </Badge>
                            )}
                          </div>
                          <h3 className="font-bold text-white mb-2">
                            {event.title}
                          </h3>
                          {event.correlation_score && (
                            <p className="text-xs text-[#A1A1AA]">
                              Correlation confidence: {(event.correlation_score * 100).toFixed(0)}%
                            </p>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Major Events Tab */}
        <TabsContent value="major" className="space-y-6">
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle>Historic Crypto Events</CardTitle>
              <CardDescription>Major events that shaped the crypto market</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {[
                  { year: '2022', event: 'FTX Collapse', impact: 'BTC -25%', type: 'bearish', desc: 'Second-largest exchange files bankruptcy' },
                  { year: '2024', event: 'Bitcoin ETF Approval', impact: 'BTC +60%', type: 'bullish', desc: 'SEC approves spot Bitcoin ETFs' },
                  { year: '2021', event: 'China Crypto Ban', impact: 'BTC -15%', type: 'bearish', desc: 'China declares all crypto transactions illegal' },
                  { year: '2021', event: 'El Salvador Adoption', impact: 'BTC +10%', type: 'bullish', desc: 'First country to make Bitcoin legal tender' },
                  { year: '2020', event: 'DeFi Summer', impact: 'ETH +400%', type: 'bullish', desc: 'Explosion of decentralized finance protocols' },
                  { year: '2022', event: 'Terra/Luna Collapse', impact: 'BTC -30%', type: 'bearish', desc: '$60B ecosystem collapse' },
                ].map((item, index) => (
                  <div 
                    key={index}
                    className="flex items-center gap-4 p-4 bg-[#121212] rounded-lg border border-[#1F1F1F]"
                  >
                    <div className="text-2xl font-data font-bold text-[#A1A1AA] w-16">
                      {item.year}
                    </div>
                    <div className={`p-2 rounded-lg ${item.type === 'bullish' ? 'bg-[#00FF94]/20' : 'bg-[#FF0055]/20'}`}>
                      {item.type === 'bullish' ? (
                        <TrendingUp className="text-[#00FF94]" />
                      ) : (
                        <TrendingDown className="text-[#FF0055]" />
                      )}
                    </div>
                    <div className="flex-1">
                      <h4 className="font-bold text-white">{item.event}</h4>
                      <p className="text-sm text-[#A1A1AA]">{item.desc}</p>
                    </div>
                    <Badge className={item.type === 'bullish' ? 'bg-[#00FF94]/20 text-[#00FF94]' : 'bg-[#FF0055]/20 text-[#FF0055]'}>
                      {item.impact}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default EventTimeline;
