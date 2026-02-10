import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BookOpen, ChevronDown, ChevronRight, Sparkles, Radar, Bot, FlaskConical, 
  Bell, Settings, TrendingUp, Brain, Zap, Shield, DollarSign, 
  BarChart3, PieChart, Users, Phone, Search, Play, Target, AlertTriangle
} from 'lucide-react';

const GuideSection = ({ title, icon: Icon, children, defaultOpen = false }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  
  return (
    <Card className="bg-[#0A0A0A] border-[#1F1F1F] overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full p-4 flex items-center justify-between hover:bg-[#121212] transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-[#00FF94]/10">
            <Icon size={20} className="text-[#00FF94]" />
          </div>
          <span className="font-bold text-white text-lg">{title}</span>
        </div>
        {isOpen ? <ChevronDown size={20} className="text-[#A1A1AA]" /> : <ChevronRight size={20} className="text-[#A1A1AA]" />}
      </button>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <CardContent className="pt-0 pb-4 px-4">
              {children}
            </CardContent>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
};

const StepItem = ({ number, title, children }) => (
  <div className="flex gap-3 mb-4">
    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#9D00FF]/20 text-[#9D00FF] flex items-center justify-center font-bold text-sm">
      {number}
    </div>
    <div>
      <h4 className="font-bold text-white mb-1">{title}</h4>
      <p className="text-sm text-[#A1A1AA]">{children}</p>
    </div>
  </div>
);

const Guide = ({ embedded = false }) => {
  return (
    <div className="p-6 lg:p-12 space-y-6" data-testid="guide-page">
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
      >
        <h1 className="text-4xl lg:text-5xl font-heading font-black tracking-tight mb-2">
          <BookOpen className="inline mr-3 text-[#00FF94]" size={48} />
          Complete <span className="text-[#00FF94]">Guide</span>
        </h1>
        <p className="text-[#A1A1AA]">Learn how to use every feature of AI Crypto Trade</p>
      </motion.div>

      {/* Quick Start */}
      <Card className="bg-gradient-to-r from-[#00FF94]/10 to-[#9D00FF]/10 border-[#00FF94]/30">
        <CardHeader>
          <CardTitle className="text-xl flex items-center gap-2">
            <Zap className="text-[#FFB800]" />
            Quick Start Guide
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-[#0A0A0A]/50 rounded-lg">
              <div className="text-2xl font-bold text-[#00FF94] mb-2">1</div>
              <h4 className="font-bold text-white mb-1">Configure API Keys</h4>
              <p className="text-sm text-[#A1A1AA]">Go to Settings → API Credentials and add your Kraken API keys</p>
            </div>
            <div className="p-4 bg-[#0A0A0A]/50 rounded-lg">
              <div className="text-2xl font-bold text-[#FFB800] mb-2">2</div>
              <h4 className="font-bold text-white mb-1">Run Gem Scanner</h4>
              <p className="text-sm text-[#A1A1AA]">Visit Gem Scanner to find high-potential crypto opportunities</p>
            </div>
            <div className="p-4 bg-[#0A0A0A]/50 rounded-lg">
              <div className="text-2xl font-bold text-[#9D00FF] mb-2">3</div>
              <h4 className="font-bold text-white mb-1">Enable Auto Trading</h4>
              <p className="text-sm text-[#A1A1AA]">Configure your risk profile and start paper trading</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="space-y-4">
        {/* Gem Scanner */}
        <GuideSection title="Hidden Gem Scanner" icon={Radar} defaultOpen={true}>
          <div className="space-y-4">
            <p className="text-[#A1A1AA]">
              The AI-powered scanner monitors 20+ cryptocurrencies in real-time, looking for patterns that historically 
              preceded 10x-100x gains. It analyzes volume, RSI, price momentum, and market sentiment.
            </p>
            
            <div className="bg-[#121212] rounded-lg p-4">
              <h4 className="font-bold text-[#FFB800] mb-3">Alert Levels Explained</h4>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Badge className="bg-[#FF0055]/20 text-[#FF0055]">HIGH</Badge>
                  <span className="text-sm text-[#A1A1AA]">Strong buy signal - Multiple indicators align (Score 60+)</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge className="bg-[#FFB800]/20 text-[#FFB800]">MEDIUM</Badge>
                  <span className="text-sm text-[#A1A1AA]">Potential opportunity - Some indicators positive (Score 40-59)</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge className="bg-[#A1A1AA]/20 text-[#A1A1AA]">LOW</Badge>
                  <span className="text-sm text-[#A1A1AA]">Watch list - Early signs of interest (Score 20-39)</span>
                </div>
              </div>
            </div>

            <StepItem number="1" title="Start Scanner">
              Go to Gem Scanner page and click "Start Scanner" to begin real-time monitoring
            </StepItem>
            <StepItem number="2" title="Manual Scan">
              Click "Scan Now" for an immediate market analysis. HIGH alerts will trigger SMS if configured.
            </StepItem>
            <StepItem number="3" title="Review Signals">
              Each alert shows matching signals like MACD_BULLISH, OVERSOLD_ACCUMULATION, EXTREME_VOLUME
            </StepItem>
          </div>
        </GuideSection>

        {/* Auto Execution */}
        <GuideSection title="Auto Execution Engine" icon={Bot}>
          <div className="space-y-4">
            <p className="text-[#A1A1AA]">
              The auto-execution engine can automatically trade when HIGH priority gems are detected. 
              It uses your risk profile to determine position sizes and manages stop-loss/take-profit automatically.
            </p>
            
            <div className="bg-[#FF0055]/10 border border-[#FF0055]/30 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle size={16} className="text-[#FF0055]" />
                <span className="font-bold text-[#FF0055]">Important</span>
              </div>
              <p className="text-sm text-[#A1A1AA]">
                Always start with PAPER mode to test strategies. Only switch to LIVE mode after you're confident 
                in the AI's performance and have verified your Kraken API permissions.
              </p>
            </div>

            <StepItem number="1" title="Configure Risk Profile">
              Set your min score (60+ recommended), max position size, stop-loss %, and take-profit %
            </StepItem>
            <StepItem number="2" title="Enable Auto-Execution">
              Click "Enable" and select PAPER mode. The AI will start executing trades automatically.
            </StepItem>
            <StepItem number="3" title="Monitor Performance">
              Watch your open positions and trade history. The AI learns from each trade outcome.
            </StepItem>
            <StepItem number="4" title="Go Live (Optional)">
              After successful paper trading, switch to LIVE mode. Ensure Kraken API has trading permissions.
            </StepItem>
          </div>
        </GuideSection>

        {/* Backtesting */}
        <GuideSection title="Backtesting Strategies" icon={FlaskConical}>
          <div className="space-y-4">
            <p className="text-[#A1A1AA]">
              Test your trading strategies against historical data before risking real money. 
              Backtesting simulates trades over the past year to show potential returns, win rates, and drawdowns.
            </p>

            <StepItem number="1" title="Configure Strategy">
              Set Min Score (signal threshold), Position % (capital per trade), Stop Loss %, and Take Profit %
            </StepItem>
            <StepItem number="2" title="Run Backtest">
              Click "Run Backtest" to simulate trades on BTC, ETH, SOL over 365 days
            </StepItem>
            <StepItem number="3" title="Analyze Results">
              Review total return, win rate, number of trades, and final portfolio value
            </StepItem>

            <div className="bg-[#121212] rounded-lg p-4">
              <h4 className="font-bold text-[#00FF94] mb-3">Key Metrics Explained</h4>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="text-[#A1A1AA]">Return:</span>
                  <span className="text-white ml-2">Total % gain/loss</span>
                </div>
                <div>
                  <span className="text-[#A1A1AA]">Win Rate:</span>
                  <span className="text-white ml-2">% of profitable trades</span>
                </div>
                <div>
                  <span className="text-[#A1A1AA]">Trades:</span>
                  <span className="text-white ml-2">Total trades executed</span>
                </div>
                <div>
                  <span className="text-[#A1A1AA]">Final Value:</span>
                  <span className="text-white ml-2">Portfolio end value</span>
                </div>
              </div>
            </div>
          </div>
        </GuideSection>

        {/* Portfolio Rebalancing */}
        <GuideSection title="Portfolio Rebalancing" icon={PieChart}>
          <div className="space-y-4">
            <p className="text-[#A1A1AA]">
              Automatically rebalance your portfolio to maintain target allocations. 
              The system calculates which trades are needed to reach your desired asset distribution.
            </p>

            <StepItem number="1" title="View Current Allocation">
              Go to Advanced → Rebalancing to see your current portfolio distribution
            </StepItem>
            <StepItem number="2" title="Review Trades Needed">
              The system shows BUY/SELL orders required to reach target allocation
            </StepItem>
            <StepItem number="3" title="Execute Rebalance">
              Click "Execute Rebalance" to automatically place the orders (paper mode first!)
            </StepItem>
          </div>
        </GuideSection>

        {/* Social Trading */}
        <GuideSection title="Social Trading & Leaderboard" icon={Users}>
          <div className="space-y-4">
            <p className="text-[#A1A1AA]">
              See how other traders are performing and learn from the best. 
              The leaderboard ranks traders by total profit percentage and win rate.
            </p>

            <StepItem number="1" title="View Leaderboard">
              Go to Advanced → Social to see top performing traders
            </StepItem>
            <StepItem number="2" title="Analyze Strategies">
              Study winning patterns - what signals do top traders follow?
            </StepItem>
            <StepItem number="3" title="Compete">
              Start trading to appear on the leaderboard. Rankings update automatically.
            </StepItem>
          </div>
        </GuideSection>

        {/* Notifications */}
        <GuideSection title="Notifications (Push & SMS)" icon={Bell}>
          <div className="space-y-4">
            <p className="text-[#A1A1AA]">
              Stay informed about your trades and high-priority opportunities with push notifications 
              and SMS alerts directly to your phone.
            </p>

            <div className="bg-[#121212] rounded-lg p-4">
              <h4 className="font-bold text-[#FFB800] mb-3">Notification Types</h4>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <Bell size={16} className="text-[#00FF94]" />
                  <span className="text-white">Push:</span>
                  <span className="text-[#A1A1AA]">In-app notifications for all trade events</span>
                </div>
                <div className="flex items-center gap-2">
                  <Phone size={16} className="text-[#FFB800]" />
                  <span className="text-white">SMS:</span>
                  <span className="text-[#A1A1AA]">Text messages for HIGH priority alerts only</span>
                </div>
              </div>
            </div>

            <StepItem number="1" title="Enable Push Notifications">
              Go to Settings → Notifications and toggle on Push Notifications
            </StepItem>
            <StepItem number="2" title="Configure SMS (Optional)">
              Add your phone number and enable SMS for high-priority alerts
            </StepItem>
            <StepItem number="3" title="Setup Twilio (For SMS)">
              To enable SMS, add your Twilio credentials to the backend .env file:
              TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
            </StepItem>
          </div>
        </GuideSection>

        {/* AI Learning */}
        <GuideSection title="AI Learning & Self-Improvement" icon={Brain}>
          <div className="space-y-4">
            <p className="text-[#A1A1AA]">
              The AI continuously learns from every trade outcome. It adjusts signal weights based on 
              which patterns lead to profitable trades, becoming smarter over time.
            </p>

            <div className="bg-[#9D00FF]/10 border border-[#9D00FF]/30 rounded-lg p-4">
              <h4 className="font-bold text-[#9D00FF] mb-2">How It Works</h4>
              <ul className="text-sm text-[#A1A1AA] space-y-1">
                <li>• Tracks profit/loss for each signal type (MACD, RSI, Volume, etc.)</li>
                <li>• Increases weight of signals that lead to profits</li>
                <li>• Decreases weight of signals that lead to losses</li>
                <li>• Generates AI insights and strategy recommendations</li>
              </ul>
            </div>

            <StepItem number="1" title="View AI Status">
              Go to Auto Execute → AI Status to see learning progress
            </StepItem>
            <StepItem number="2" title="Check Signal Weights">
              View which signals are performing best (weight &gt; 1.0 = above average)
            </StepItem>
            <StepItem number="3" title="Get AI Insights">
              Click "AI Insights" for personalized strategy recommendations
            </StepItem>
          </div>
        </GuideSection>

        {/* Settings & API */}
        <GuideSection title="Settings & API Configuration" icon={Settings}>
          <div className="space-y-4">
            <p className="text-[#A1A1AA]">
              Configure your exchange API keys, risk parameters, and notification preferences.
            </p>

            <StepItem number="1" title="Add Kraken API Keys">
              Get your API keys from Kraken (Settings → API → Generate New Key). 
              Enable: Query Funds, Create Orders, Cancel Orders. NEVER enable Withdraw.
            </StepItem>
            <StepItem number="2" title="Set Risk Parameters">
              Configure max investment per trade, stop-loss %, take-profit %, and risk level
            </StepItem>
            <StepItem number="3" title="Configure Notifications">
              Enable/disable push and SMS notifications for trades and alerts
            </StepItem>
          </div>
        </GuideSection>

        {/* Tips & Best Practices */}
        <GuideSection title="Tips & Best Practices" icon={Target}>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-[#00FF94]/10 border border-[#00FF94]/30 rounded-lg p-4">
                <h4 className="font-bold text-[#00FF94] mb-2">✅ Do</h4>
                <ul className="text-sm text-[#A1A1AA] space-y-1">
                  <li>• Start with paper trading</li>
                  <li>• Use backtesting before live trading</li>
                  <li>• Set strict stop-losses (10-15%)</li>
                  <li>• Diversify across multiple coins</li>
                  <li>• Review AI performance weekly</li>
                </ul>
              </div>
              <div className="bg-[#FF0055]/10 border border-[#FF0055]/30 rounded-lg p-4">
                <h4 className="font-bold text-[#FF0055] mb-2">❌ Don't</h4>
                <ul className="text-sm text-[#A1A1AA] space-y-1">
                  <li>• Never enable API withdraw permission</li>
                  <li>• Don't risk more than you can lose</li>
                  <li>• Don't ignore stop-loss limits</li>
                  <li>• Don't chase every alert</li>
                  <li>• Don't skip the learning period</li>
                </ul>
              </div>
            </div>

            <div className="bg-[#007AFF]/10 border border-[#007AFF]/30 rounded-lg p-4">
              <h4 className="font-bold text-[#007AFF] mb-2">💡 Pro Tips</h4>
              <ul className="text-sm text-[#A1A1AA] space-y-1">
                <li>• HIGH alerts with score 70+ have the best historical performance</li>
                <li>• OVERSOLD_ACCUMULATION + EXTREME_VOLUME is a powerful combination</li>
                <li>• Let the AI paper trade for at least 2 weeks before going live</li>
                <li>• Check the leaderboard to see what top traders are doing</li>
                <li>• Use smaller position sizes (5-10%) to manage risk</li>
              </ul>
            </div>
          </div>
        </GuideSection>
      </div>
    </div>
  );
};

export default Guide;
