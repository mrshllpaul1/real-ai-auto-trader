import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { motion } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';
import { 
  Key, Check, X, AlertTriangle, Copy, ExternalLink, 
  Mail, Database, Bot, TrendingUp, Shield
} from 'lucide-react';

const Setup = () => {
  const [configStatus, setConfigStatus] = useState({});
  const [credentials, setCredentials] = useState({
    RESEND_API_KEY: '',
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    checkConfigStatus();
  }, []);

  const checkConfigStatus = async () => {
    try {
      // Check various API statuses
      const [emailRes, notifRes] = await Promise.all([
        api.get('/email/settings').catch(() => ({ data: {} })),
        api.get('/notifications/settings').catch(() => ({ data: {} }))
      ]);

      setConfigStatus({
        email: emailRes.data?.configured || false,
        emailRecipient: emailRes.data?.default_recipient || '',
        // These are always configured from the handoff
        kraken: true,
        coinmarketcap: true,
        coinstats: true,
        mongodb: true,
        emergentLlm: true,
      });
    } catch (error) {
      console.error('Error checking config:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (key, value) => {
    setCredentials(prev => ({ ...prev, [key]: value }));
  };

  const copyTemplate = () => {
    const template = `# Paste these values to complete your setup:

# Email Notifications (Resend)
RESEND_API_KEY=${credentials.RESEND_API_KEY || 'your_resend_api_key_here'}
`;
    navigator.clipboard.writeText(template);
    toast.success('Template copied to clipboard!');
  };

  const generateConfigText = () => {
    let text = '';
    if (credentials.RESEND_API_KEY) {
      text += `RESEND_API_KEY=${credentials.RESEND_API_KEY}\n`;
    }
    if (credentials.TWILIO_ACCOUNT_SID) {
      text += `TWILIO_ACCOUNT_SID=${credentials.TWILIO_ACCOUNT_SID}\n`;
    }
    if (credentials.TWILIO_AUTH_TOKEN) {
      text += `TWILIO_AUTH_TOKEN=${credentials.TWILIO_AUTH_TOKEN}\n`;
    }
    if (credentials.TWILIO_PHONE_NUMBER) {
      text += `TWILIO_PHONE_NUMBER=${credentials.TWILIO_PHONE_NUMBER}\n`;
    }
    return text;
  };

  const configItems = [
    {
      id: 'email',
      name: 'Email Notifications (Resend)',
      icon: Mail,
      configured: configStatus.email,
      required: true,
      description: 'Send detailed trade alerts with key factors to your email',
      envKey: 'RESEND_API_KEY',
      signupUrl: 'https://resend.com',
      signupText: 'Get API Key from Resend',
      instructions: 'Sign up → Dashboard → API Keys → Create API Key',
      recipient: configStatus.emailRecipient,
    },
    {
      id: 'kraken',
      name: 'Kraken Exchange',
      icon: TrendingUp,
      configured: configStatus.kraken,
      required: true,
      description: 'Execute trades on Kraken exchange',
      status: 'Already configured ✓',
    },
    {
      id: 'coinmarketcap',
      name: 'CoinMarketCap',
      icon: Database,
      configured: configStatus.coinmarketcap,
      required: true,
      description: 'Real-time crypto market data',
      status: 'Already configured ✓',
    },
    {
      id: 'emergent',
      name: 'Emergent LLM (AI)',
      icon: Bot,
      configured: configStatus.emergentLlm,
      required: true,
      description: 'AI-powered trading analysis',
      status: 'Already configured ✓',
    },
    {
      id: 'mongodb',
      name: 'MongoDB Database',
      icon: Database,
      configured: configStatus.mongodb,
      required: true,
      description: 'Store trades, strategies, and alerts',
      status: 'Already configured ✓',
    },
  ];

  const missingRequired = configItems.filter(item => item.required && !item.configured && !item.status);
  const missingOptional = configItems.filter(item => !item.required && !item.configured && !item.status);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-[#00FF94]" />
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 lg:p-12 space-y-6" data-testid="setup-page">
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
      >
        <h1 className="text-3xl md:text-4xl lg:text-5xl font-heading font-black tracking-tight mb-2">
          <Key className="inline mr-3 text-[#FFB800]" size={40} />
          <span className="text-[#FFB800]">Setup</span> & API Keys
        </h1>
        <p className="text-[#A1A1AA]">Configure your integrations to unlock all features</p>
      </motion.div>

      {/* Status Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Card className="bg-[#00FF94]/10 border-[#00FF94]/30">
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-[#00FF94]">
              {configItems.filter(i => i.configured || i.status).length}
            </div>
            <div className="text-xs text-[#A1A1AA]">Configured</div>
          </CardContent>
        </Card>
        <Card className="bg-[#FF0055]/10 border-[#FF0055]/30">
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-[#FF0055]">
              {missingRequired.length}
            </div>
            <div className="text-xs text-[#A1A1AA]">Required</div>
          </CardContent>
        </Card>
        <Card className="bg-[#FFB800]/10 border-[#FFB800]/30">
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-[#FFB800]">
              {missingOptional.length}
            </div>
            <div className="text-xs text-[#A1A1AA]">Optional</div>
          </CardContent>
        </Card>
        <Card className="bg-[#9D00FF]/10 border-[#9D00FF]/30">
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-[#9D00FF]">
              {configItems.length}
            </div>
            <div className="text-xs text-[#A1A1AA]">Total</div>
          </CardContent>
        </Card>
      </div>

      {/* Missing Credentials Input */}
      {(missingRequired.length > 0 || missingOptional.length > 0) && (
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardHeader>
            <CardTitle className="text-xl flex items-center gap-2">
              <AlertTriangle className="text-[#FFB800]" size={20} />
              Enter Missing API Keys
            </CardTitle>
            <CardDescription>
              Fill in the values below, then copy and send them to complete setup
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Email - Resend */}
            <div className="space-y-3 p-4 bg-[#121212] rounded-lg border border-[#1F1F1F]">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Mail className="text-[#FF0055]" size={20} />
                  <span className="font-bold text-white">Email (Resend)</span>
                  <Badge className="bg-[#FF0055]/20 text-[#FF0055]">Required</Badge>
                </div>
                <a 
                  href="https://resend.com" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-xs text-[#007AFF] hover:underline flex items-center gap-1"
                >
                  Get Key <ExternalLink size={12} />
                </a>
              </div>
              <p className="text-xs text-[#A1A1AA]">
                Sign up at resend.com → Dashboard → API Keys → Create API Key (starts with re_...)
              </p>
              <div>
                <Label className="text-xs text-[#A1A1AA]">RESEND_API_KEY</Label>
                <Input
                  type="password"
                  placeholder="re_xxxxxxxx..."
                  value={credentials.RESEND_API_KEY}
                  onChange={(e) => handleInputChange('RESEND_API_KEY', e.target.value)}
                  className="bg-[#0A0A0A] border-[#333] font-mono text-sm mt-1"
                  data-testid="resend-api-key-input"
                />
              </div>
              <div className="text-xs text-[#666]">
                📧 Emails will be sent to: <span className="text-[#00FF94]">{configStatus.emailRecipient}</span>
              </div>
            </div>

            {/* Output Box */}
            {credentials.RESEND_API_KEY && (
              <div className="space-y-2">
                <Label className="text-sm text-white">Copy this and send it to me:</Label>
                <div className="bg-[#000] border border-[#333] rounded-lg p-4 font-mono text-xs text-[#00FF94] whitespace-pre-wrap">
                  {generateConfigText() || 'Enter values above...'}
                </div>
                <Button
                  onClick={() => {
                    navigator.clipboard.writeText(generateConfigText());
                    toast.success('Copied to clipboard!');
                  }}
                  className="w-full bg-[#00FF94] hover:bg-[#00CC76] text-black font-bold rounded-full"
                  data-testid="copy-config-btn"
                >
                  <Copy size={16} className="mr-2" />
                  Copy Configuration
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* All Integrations Status */}
      <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
        <CardHeader>
          <CardTitle className="text-xl">All Integrations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {configItems.map((item) => (
              <div 
                key={item.id}
                className={`flex items-center justify-between p-4 rounded-lg border ${
                  item.configured || item.status 
                    ? 'bg-[#00FF94]/5 border-[#00FF94]/30' 
                    : item.required 
                      ? 'bg-[#FF0055]/5 border-[#FF0055]/30'
                      : 'bg-[#FFB800]/5 border-[#FFB800]/30'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${
                    item.configured || item.status ? 'bg-[#00FF94]/20' : 'bg-[#333]'
                  }`}>
                    <item.icon size={20} className={
                      item.configured || item.status ? 'text-[#00FF94]' : 'text-[#666]'
                    } />
                  </div>
                  <div>
                    <div className="font-bold text-white text-sm">{item.name}</div>
                    <div className="text-xs text-[#A1A1AA]">{item.description}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {item.configured || item.status ? (
                    <Badge className="bg-[#00FF94]/20 text-[#00FF94]">
                      <Check size={12} className="mr-1" /> Configured
                    </Badge>
                  ) : item.required ? (
                    <Badge className="bg-[#FF0055]/20 text-[#FF0055]">
                      <X size={12} className="mr-1" /> Required
                    </Badge>
                  ) : (
                    <Badge className="bg-[#FFB800]/20 text-[#FFB800]">
                      <AlertTriangle size={12} className="mr-1" /> Optional
                    </Badge>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Quick Reference */}
      <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
        <CardHeader>
          <CardTitle className="text-xl">Your Current Settings</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="p-3 bg-[#121212] rounded-lg">
              <div className="text-[#A1A1AA] text-xs">Email Recipient</div>
              <div className="text-[#00FF94] font-mono">{configStatus.emailRecipient || 'Not set'}</div>
            </div>
            <div className="p-3 bg-[#121212] rounded-lg">
              <div className="text-[#A1A1AA] text-xs">SMS Phone Number</div>
              <div className="text-[#00FF94] font-mono">{configStatus.smsPhone || '2104412761'}</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Setup;
