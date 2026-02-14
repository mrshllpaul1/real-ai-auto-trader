/**
 * Login Page - Social Login with Google OAuth
 * REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Zap, Shield, Brain, TrendingUp, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';

const LoginPage = () => {
  const handleGoogleLogin = () => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = window.location.origin + '/';
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  const features = [
    { icon: Brain, title: 'AI-Powered Trading', desc: 'Advanced ML models for market prediction' },
    { icon: TrendingUp, title: 'Real-Time Analytics', desc: 'Live portfolio tracking and signals' },
    { icon: Shield, title: 'Secure & Private', desc: 'Bank-level encryption for your data' },
  ];

  return (
    <div className="min-h-screen bg-[#0A0A0A] flex">
      {/* Left Panel - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-slate-900 via-slate-900 to-cyan-950 p-12 flex-col justify-between">
        <div>
          <motion.h1 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-4xl font-black"
          >
            <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">AI</span>
            <span className="text-white">Crypto</span>
            <span className="bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">Trade</span>
            <Zap className="inline-block ml-2 text-yellow-400 w-8 h-8" />
          </motion.h1>
          <p className="text-gray-400 mt-2">Real Money Auto Trading Platform</p>
        </div>

        <div className="space-y-6">
          {features.map((feature, i) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 + i * 0.1 }}
              className="flex items-start gap-4"
            >
              <div className="p-3 rounded-xl bg-gradient-to-br from-cyan-500/20 to-emerald-500/10 border border-cyan-500/20">
                <feature.icon className="w-6 h-6 text-cyan-400" />
              </div>
              <div>
                <h3 className="text-white font-semibold">{feature.title}</h3>
                <p className="text-gray-500 text-sm">{feature.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>

        <div className="text-gray-600 text-sm">
          © 2026 AICryptoTrade. All rights reserved.
        </div>
      </div>

      {/* Right Panel - Login Form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="w-full max-w-md"
        >
          {/* Mobile Logo */}
          <div className="lg:hidden text-center mb-8">
            <h1 className="text-3xl font-black">
              <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">AI</span>
              <span className="text-white">Crypto</span>
              <span className="bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">Trade</span>
            </h1>
          </div>

          <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl p-8 border border-slate-700/50 shadow-2xl">
            <h2 className="text-2xl font-bold text-white mb-2">Welcome</h2>
            <p className="text-gray-400 mb-8">Sign in to access your trading dashboard</p>

            {/* Google Sign In Button */}
            <Button
              onClick={handleGoogleLogin}
              className="w-full py-6 bg-white hover:bg-gray-100 text-gray-900 font-medium rounded-xl flex items-center justify-center gap-3 transition-all duration-200 shadow-lg hover:shadow-xl"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Continue with Google
              <ChevronRight className="w-4 h-4" />
            </Button>

            <div className="mt-6 text-center">
              <p className="text-gray-500 text-sm">
                By signing in, you agree to our{' '}
                <a href="#" className="text-cyan-400 hover:text-cyan-300">Terms of Service</a>
                {' '}and{' '}
                <a href="#" className="text-cyan-400 hover:text-cyan-300">Privacy Policy</a>
              </p>
            </div>
          </div>

          {/* Demo Mode */}
          <div className="mt-6 text-center">
            <button
              onClick={() => {
                localStorage.setItem('user_id', 'demo_user_' + Date.now());
                localStorage.setItem('user_name', 'Demo User');
                localStorage.setItem('authenticated', 'demo');
                window.location.href = '/';
              }}
              className="text-gray-500 hover:text-gray-400 text-sm transition-colors"
            >
              Continue as Guest (Demo Mode)
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default LoginPage;
