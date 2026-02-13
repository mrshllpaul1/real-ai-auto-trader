import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Zap, Loader2, Power, Clock, Calendar, DollarSign } from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';

const AutopilotControl = ({ mode }) => {
  const [schedulerStatus, setSchedulerStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Determine if paper mode based on prop or localStorage
  const isPaperMode = mode === 'paper' || (mode === undefined && localStorage.getItem('growth_trading_mode') !== 'real');

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 60000);
    return () => clearInterval(interval);
  }, []);

  const loadStatus = async () => {
    try {
      const response = await api.get('/scheduler/status');
      setSchedulerStatus(response.data);
    } catch (error) {
      console.error('Scheduler status error:', error);
    }
  };

  const setupAutoPilot = async () => {
    setLoading(true);
    try {
      const response = await api.post(`/scheduler/setup-default?paper_trade=${isPaperMode}`);
      if (response.data.success) {
        toast.success('Autopilot activated! Passive income mode ON');
        loadStatus();
      }
    } catch (error) {
      toast.error('Failed to setup autopilot');
    } finally {
      setLoading(false);
    }
  };

  const stopScheduler = async () => {
    setLoading(true);
    try {
      await api.post('/scheduler/stop');
      toast.info('Scheduler stopped');
      loadStatus();
    } catch (error) {
      toast.error('Failed to stop scheduler');
    } finally {
      setLoading(false);
    }
  };

  const startScheduler = async () => {
    setLoading(true);
    try {
      await api.post('/scheduler/start');
      toast.success('Scheduler started');
      loadStatus();
    } catch (error) {
      toast.error('Failed to start scheduler');
    } finally {
      setLoading(false);
    }
  };

  const isActive = schedulerStatus?.running && schedulerStatus?.job_count > 0;
  const jobs = schedulerStatus?.jobs || [];

  return (
    <motion.div
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay: 0.38 }}
      className="mb-8"
    >
      <Card className="bg-gradient-to-r from-[#9D00FF]/10 to-[#007AFF]/10 border-[#9D00FF]/30">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Zap className="text-[#9D00FF]" />
            Autopilot Mode
            {isActive && (
              <Badge className="bg-[#00FF94]/20 text-[#00FF94] ml-2">ACTIVE</Badge>
            )}
          </CardTitle>
          <CardDescription className="text-[#A1A1AA]">
            Let AI trade automatically while you sleep
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-center gap-4 mb-4">
            <Button
              onClick={setupAutoPilot}
              disabled={loading}
              className="bg-[#9D00FF] hover:bg-[#7B00CC] text-white font-bold"
              data-testid="autopilot-btn"
            >
              {loading ? <Loader2 className="animate-spin mr-2" /> : <Zap className="mr-2" />}
              Activate Autopilot
            </Button>
            
            {schedulerStatus?.running ? (
              <Button
                onClick={stopScheduler}
                disabled={loading}
                variant="outline"
                className="border-[#FF0055] text-[#FF0055]"
              >
                <Power className="mr-2" size={16} />
                Stop
              </Button>
            ) : (
              <Button
                onClick={startScheduler}
                disabled={loading}
                variant="outline"
                className="border-[#00FF94] text-[#00FF94]"
              >
                <Power className="mr-2" size={16} />
                Start
              </Button>
            )}
          </div>
          
          {jobs.length > 0 && (
            <div className="space-y-2">
              <div className="text-sm text-[#A1A1AA] mb-2">Scheduled Jobs:</div>
              {jobs.map((job, i) => {
                let Icon = Clock;
                let color = 'text-[#007AFF]';
                if (job.id === 'weekly_trader') {
                  Icon = Calendar;
                  color = 'text-[#FF9500]';
                } else if (job.id === 'daily_compound') {
                  Icon = DollarSign;
                  color = 'text-[#00FF94]';
                }
                
                return (
                  <div key={i} className="flex items-center justify-between p-2 bg-[#121212] rounded-lg text-sm">
                    <div className="flex items-center gap-2">
                      <Icon size={14} className={color} />
                      <span>{job.name}</span>
                    </div>
                    <span className="text-[#A1A1AA]">
                      Next: {job.next_run ? new Date(job.next_run).toLocaleString() : 'N/A'}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default AutopilotControl;
