/**
 * OnboardingTour - Interactive walkthrough for new users
 * Highlights key features with step-by-step tooltips
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, ChevronRight, ChevronLeft, Check, 
  LayoutDashboard, Radio, Wallet, Brain, 
  BarChart3, Shield, Rocket, Sparkles 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL || '';

const TOUR_STEPS = [
  {
    id: 'welcome',
    title: 'Welcome to AICryptoTrade! 🚀',
    description: 'Your AI-powered crypto trading platform. Let me show you around.',
    icon: Sparkles,
    color: 'cyan',
    position: 'center',
  },
  {
    id: 'command-center',
    title: 'Command Center',
    description: 'Your main dashboard showing portfolio value, holdings, and market overview at a glance.',
    icon: LayoutDashboard,
    color: 'cyan',
    target: '[data-tour="command-center"]',
    position: 'right',
  },
  {
    id: 'live-dashboard',
    title: 'Live Dashboard',
    description: 'Real-time P&L tracking with live AI signals. Watch your portfolio update in real-time.',
    icon: Radio,
    color: 'emerald',
    target: '[data-tour="live-dashboard"]',
    position: 'right',
  },
  {
    id: 'trading',
    title: 'Trading Hub',
    description: 'Execute trades, manage positions, and set up advanced orders. Your trading command center.',
    icon: Wallet,
    color: 'emerald',
    target: '[data-tour="trading"]',
    position: 'right',
  },
  {
    id: 'ai-strategy',
    title: 'AI & Strategy',
    description: 'Access AI-powered trading signals, strategy builders, and machine learning models.',
    icon: Brain,
    color: 'violet',
    target: '[data-tour="ai-strategy"]',
    position: 'right',
  },
  {
    id: 'backtest',
    title: 'Backtesting',
    description: 'Test your strategies against historical data before risking real money.',
    icon: BarChart3,
    color: 'blue',
    target: '[data-tour="backtest"]',
    position: 'right',
  },
  {
    id: 'security',
    title: 'Security First',
    description: 'Your funds are protected with encryption. Enable 2FA in Settings for extra security.',
    icon: Shield,
    color: 'amber',
    position: 'center',
  },
  {
    id: 'complete',
    title: "You're All Set! 🎉",
    description: 'Start exploring and let AI help you trade smarter. Good luck!',
    icon: Rocket,
    color: 'emerald',
    position: 'center',
  },
];

const OnboardingTour = ({ isOpen, onClose, onComplete }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isVisible, setIsVisible] = useState(isOpen);

  useEffect(() => {
    setIsVisible(isOpen);
    if (isOpen) {
      setCurrentStep(0);
    }
  }, [isOpen]);

  const step = TOUR_STEPS[currentStep];
  const progress = ((currentStep + 1) / TOUR_STEPS.length) * 100;

  const handleNext = () => {
    if (currentStep < TOUR_STEPS.length - 1) {
      setCurrentStep(prev => prev + 1);
    } else {
      handleComplete();
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const handleSkip = () => {
    handleComplete();
  };

  const handleComplete = async () => {
    try {
      await fetch(`${BACKEND_URL}/api/auth/onboarding/complete`, {
        method: 'POST',
        credentials: 'include',
      });
    } catch (e) {
      console.warn('Failed to mark onboarding complete:', e);
    }
    
    setIsVisible(false);
    onComplete?.();
    onClose?.();
  };

  const colorMap = {
    cyan: 'from-cyan-500/20 to-cyan-500/5 border-cyan-500/30 text-cyan-400',
    emerald: 'from-emerald-500/20 to-emerald-500/5 border-emerald-500/30 text-emerald-400',
    violet: 'from-violet-500/20 to-violet-500/5 border-violet-500/30 text-violet-400',
    blue: 'from-blue-500/20 to-blue-500/5 border-blue-500/30 text-blue-400',
    amber: 'from-amber-500/20 to-amber-500/5 border-amber-500/30 text-amber-400',
  };

  if (!isVisible) return null;

  const Icon = step.icon;

  return (
    <AnimatePresence>
      {isVisible && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[100]"
            onClick={handleSkip}
          />

          {/* Tour Card */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-[101] w-full max-w-md px-4"
          >
            <div className={`bg-gradient-to-br ${colorMap[step.color]} rounded-2xl border shadow-2xl overflow-hidden`}>
              {/* Header */}
              <div className="p-6 pb-4">
                <div className="flex items-start justify-between mb-4">
                  <div className={`p-3 rounded-xl bg-gradient-to-br ${colorMap[step.color]}`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <button
                    onClick={handleSkip}
                    className="p-2 rounded-lg hover:bg-white/10 transition-colors text-gray-400 hover:text-white"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <h2 className="text-xl font-bold text-white mb-2">{step.title}</h2>
                <p className="text-gray-300">{step.description}</p>
              </div>

              {/* Progress */}
              <div className="px-6">
                <div className="flex items-center gap-2 mb-2">
                  <Progress value={progress} className="h-1.5 flex-1" />
                  <span className="text-xs text-gray-500">
                    {currentStep + 1}/{TOUR_STEPS.length}
                  </span>
                </div>
              </div>

              {/* Actions */}
              <div className="p-6 pt-4 flex items-center justify-between bg-black/20">
                <button
                  onClick={handleSkip}
                  className="text-sm text-gray-500 hover:text-gray-300 transition-colors"
                >
                  Skip tour
                </button>

                <div className="flex items-center gap-2">
                  {currentStep > 0 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handlePrev}
                      className="text-gray-400"
                    >
                      <ChevronLeft className="w-4 h-4 mr-1" />
                      Back
                    </Button>
                  )}
                  
                  <Button
                    onClick={handleNext}
                    size="sm"
                    className={`${
                      step.color === 'cyan' ? 'bg-cyan-600 hover:bg-cyan-700' :
                      step.color === 'emerald' ? 'bg-emerald-600 hover:bg-emerald-700' :
                      step.color === 'violet' ? 'bg-violet-600 hover:bg-violet-700' :
                      step.color === 'blue' ? 'bg-blue-600 hover:bg-blue-700' :
                      'bg-amber-600 hover:bg-amber-700'
                    }`}
                  >
                    {currentStep === TOUR_STEPS.length - 1 ? (
                      <>
                        <Check className="w-4 h-4 mr-1" />
                        Get Started
                      </>
                    ) : (
                      <>
                        Next
                        <ChevronRight className="w-4 h-4 ml-1" />
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </div>

            {/* Step Indicators */}
            <div className="flex justify-center gap-1.5 mt-4">
              {TOUR_STEPS.map((_, i) => (
                <button
                  key={i}
                  onClick={() => setCurrentStep(i)}
                  className={`w-2 h-2 rounded-full transition-all ${
                    i === currentStep 
                      ? 'bg-white w-6' 
                      : i < currentStep 
                        ? 'bg-white/50' 
                        : 'bg-white/20'
                  }`}
                />
              ))}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default OnboardingTour;
