import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  ChevronRight, ChevronLeft, CheckCircle, Circle, Rocket, 
  Key, Brain, Zap, DollarSign, Shield, Target, ArrowRight
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const tutorialSteps = [
  {
    id: 1,
    title: "Welcome to AI Crypto Trading",
    description: "Your journey to turning $500 into $100,000 starts here",
    icon: Rocket,
    content: (
      <div className="space-y-4">
        <p className="text-[#A1A1AA]">
          This AI-powered trading platform uses advanced algorithms trained on 11+ years of crypto market data 
          to find the best trading opportunities.
        </p>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-[#121212] rounded-lg">
            <div className="text-2xl font-bold text-[#00FF94]">59.5%</div>
            <div className="text-sm text-[#A1A1AA]">Win Rate</div>
          </div>
          <div className="p-4 bg-[#121212] rounded-lg">
            <div className="text-2xl font-bold text-[#007AFF]">200x</div>
            <div className="text-sm text-[#A1A1AA]">Target Return</div>
          </div>
        </div>
      </div>
    )
  },
  {
    id: 2,
    title: "Set Your Budget",
    description: "The AI only uses what you allocate - your other assets are safe",
    icon: Shield,
    content: (
      <div className="space-y-4">
        <div className="p-4 bg-[#00FF94]/10 border border-[#00FF94]/30 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Shield className="text-[#00FF94]" size={20} />
            <span className="font-bold text-[#00FF94]">Budget Protection</span>
          </div>
          <p className="text-sm text-[#A1A1AA]">
            The AI will NEVER touch your other assets. It only uses the exact budget you allocate.
            Start with paper trading ($500 virtual) to see how it works risk-free.
          </p>
        </div>
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <CheckCircle className="text-[#00FF94]" size={16} />
            <span className="text-sm">Paper Trading: $500 virtual money (no risk)</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle className="text-[#00FF94]" size={16} />
            <span className="text-sm">Real Trading: Only uses your allocated budget</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle className="text-[#00FF94]" size={16} />
            <span className="text-sm">Your other Kraken assets remain untouched</span>
          </div>
        </div>
      </div>
    )
  },
  {
    id: 3,
    title: "Connect Kraken (Optional)",
    description: "Link your exchange for real trading when you're ready",
    icon: Key,
    content: (
      <div className="space-y-4">
        <p className="text-[#A1A1AA]">
          To enable real money trading, you&apos;ll need to add your Kraken API credentials.
          This is optional - you can use paper trading indefinitely.
        </p>
        <div className="p-4 bg-[#121212] rounded-lg space-y-3">
          <div className="text-sm font-bold">How to get Kraken API keys:</div>
          <ol className="text-sm text-[#A1A1AA] space-y-2 list-decimal list-inside">
            <li>Log in to Kraken.com</li>
            <li>Go to Settings → API</li>
            <li>Create a new API key</li>
            <li>Enable &quot;Query Funds&quot; and &quot;Create &amp; Modify Orders&quot;</li>
            <li>Add keys in Settings page of this app</li>
          </ol>
        </div>
        <Badge className="bg-[#FF9500]/20 text-[#FF9500]">
          Skip this step to continue with paper trading
        </Badge>
      </div>
    )
  },
  {
    id: 4,
    title: "AI Training & Strategy",
    description: "The AI learns from historical data to make smart decisions",
    icon: Brain,
    content: (
      <div className="space-y-4">
        <p className="text-[#A1A1AA]">
          Our AI has been trained on crypto market data from 2014 to present, learning patterns
          that lead to profitable trades.
        </p>
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 bg-[#121212] rounded-lg">
            <div className="text-lg font-bold text-[#00FF94]">62,000+</div>
            <div className="text-xs text-[#A1A1AA]">Historical Records</div>
          </div>
          <div className="p-3 bg-[#121212] rounded-lg">
            <div className="text-lg font-bold text-[#007AFF]">37</div>
            <div className="text-xs text-[#A1A1AA]">Coins Analyzed</div>
          </div>
          <div className="p-3 bg-[#121212] rounded-lg">
            <div className="text-lg font-bold text-[#9D00FF]">11+</div>
            <div className="text-xs text-[#A1A1AA]">Years of Data</div>
          </div>
          <div className="p-3 bg-[#121212] rounded-lg">
            <div className="text-lg font-bold text-[#FFD700]">Hidden Gems</div>
            <div className="text-xs text-[#A1A1AA]">10-100x Potential</div>
          </div>
        </div>
      </div>
    )
  },
  {
    id: 5,
    title: "Activate Autopilot",
    description: "Let the AI trade automatically while you sleep",
    icon: Zap,
    content: (
      <div className="space-y-4">
        <p className="text-[#A1A1AA]">
          Once configured, the AI runs 24/7 monitoring the market and executing trades automatically.
        </p>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-[#121212] rounded-lg">
            <div className="flex items-center gap-2">
              <Target className="text-[#007AFF]" size={16} />
              <span className="text-sm">Position Monitoring</span>
            </div>
            <Badge className="bg-[#007AFF]/20 text-[#007AFF]">Every Hour</Badge>
          </div>
          <div className="flex items-center justify-between p-3 bg-[#121212] rounded-lg">
            <div className="flex items-center gap-2">
              <DollarSign className="text-[#00FF94]" size={16} />
              <span className="text-sm">Profit Compounding</span>
            </div>
            <Badge className="bg-[#00FF94]/20 text-[#00FF94]">Daily</Badge>
          </div>
          <div className="flex items-center justify-between p-3 bg-[#121212] rounded-lg">
            <div className="flex items-center gap-2">
              <Brain className="text-[#9D00FF]" size={16} />
              <span className="text-sm">Strategy Rebalancing</span>
            </div>
            <Badge className="bg-[#9D00FF]/20 text-[#9D00FF]">Weekly</Badge>
          </div>
        </div>
      </div>
    )
  },
  {
    id: 6,
    title: "You're Ready!",
    description: "Start your journey to $100,000",
    icon: Rocket,
    content: (
      <div className="space-y-4 text-center">
        <div className="text-6xl mb-4">🚀</div>
        <h3 className="text-2xl font-bold text-[#00FF94]">Ready to Begin!</h3>
        <p className="text-[#A1A1AA]">
          Head to the Growth Dashboard to deploy your first $500 and watch the AI work its magic.
        </p>
        <div className="p-4 bg-gradient-to-r from-[#00FF94]/20 to-[#007AFF]/20 rounded-lg">
          <div className="text-sm text-[#A1A1AA] mb-2">Recommended first steps:</div>
          <div className="space-y-2 text-left">
            <div className="flex items-center gap-2">
              <ArrowRight className="text-[#00FF94]" size={14} />
              <span className="text-sm">Start with Paper Trading to learn</span>
            </div>
            <div className="flex items-center gap-2">
              <ArrowRight className="text-[#00FF94]" size={14} />
              <span className="text-sm">Activate Autopilot for passive income</span>
            </div>
            <div className="flex items-center gap-2">
              <ArrowRight className="text-[#00FF94]" size={14} />
              <span className="text-sm">Monitor the dashboard daily</span>
            </div>
          </div>
        </div>
      </div>
    )
  }
];

const UserTutorial = ({ onComplete, onSkip }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState([]);
  
  const step = tutorialSteps[currentStep];
  const progress = ((currentStep + 1) / tutorialSteps.length) * 100;
  const Icon = step.icon;
  
  const nextStep = () => {
    if (!completedSteps.includes(currentStep)) {
      setCompletedSteps([...completedSteps, currentStep]);
    }
    if (currentStep < tutorialSteps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      onComplete?.();
    }
  };
  
  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };
  
  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="w-full max-w-lg"
      >
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardHeader>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                {tutorialSteps.map((s, i) => (
                  <div
                    key={i}
                    className={`w-2 h-2 rounded-full transition-colors ${
                      i === currentStep ? 'bg-[#00FF94]' : 
                      completedSteps.includes(i) ? 'bg-[#007AFF]' : 'bg-[#333]'
                    }`}
                  />
                ))}
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={onSkip}
                className="text-[#A1A1AA] hover:text-white"
              >
                Skip Tutorial
              </Button>
            </div>
            
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-[#00FF94]/20 rounded-lg">
                <Icon className="text-[#00FF94]" size={24} />
              </div>
              <div>
                <CardTitle className="text-xl">{step.title}</CardTitle>
                <CardDescription className="text-[#A1A1AA]">{step.description}</CardDescription>
              </div>
            </div>
            
            <Progress value={progress} className="h-1 bg-[#1F1F1F]" />
          </CardHeader>
          
          <CardContent>
            <AnimatePresence mode="wait">
              <motion.div
                key={currentStep}
                initial={{ x: 20, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: -20, opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                {step.content}
              </motion.div>
            </AnimatePresence>
            
            <div className="flex items-center justify-between mt-6 pt-4 border-t border-[#1F1F1F]">
              <Button
                variant="ghost"
                onClick={prevStep}
                disabled={currentStep === 0}
                className="text-[#A1A1AA]"
              >
                <ChevronLeft size={16} className="mr-1" />
                Back
              </Button>
              
              <Button
                onClick={nextStep}
                className="bg-[#00FF94] hover:bg-[#00CC77] text-black font-bold"
              >
                {currentStep === tutorialSteps.length - 1 ? 'Get Started' : 'Next'}
                <ChevronRight size={16} className="ml-1" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export default UserTutorial;
