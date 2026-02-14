/**
 * SecuritySettings - 2FA Setup and Session Management
 */

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Shield, Smartphone, Key, LogOut, AlertTriangle, 
  Check, Copy, Eye, EyeOff, RefreshCw, Loader2 
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL || '';

const SecuritySettings = () => {
  const [loading, setLoading] = useState(true);
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false);
  const [setupData, setSetupData] = useState(null);
  const [verificationCode, setVerificationCode] = useState('');
  const [showBackupCodes, setShowBackupCodes] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    fetchSecurityStatus();
  }, []);

  const fetchSecurityStatus = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/auth/me`, {
        credentials: 'include',
      });
      if (response.ok) {
        const data = await response.json();
        setTwoFactorEnabled(data.two_factor_enabled || false);
      }

      const sessionsRes = await fetch(`${BACKEND_URL}/api/auth/sessions`, {
        credentials: 'include',
      });
      if (sessionsRes.ok) {
        const sessionsData = await sessionsRes.json();
        setSessions(sessionsData.sessions || []);
      }
    } catch (error) {
      console.error('Failed to fetch security status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSetup2FA = async () => {
    setProcessing(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/auth/2fa/setup`, {
        method: 'POST',
        credentials: 'include',
      });
      
      if (!response.ok) throw new Error('Failed to setup 2FA');
      
      const data = await response.json();
      setSetupData(data);
      toast.success('Scan the QR code with your authenticator app');
    } catch (error) {
      toast.error('Failed to setup 2FA');
    } finally {
      setProcessing(false);
    }
  };

  const handleVerify2FA = async () => {
    if (verificationCode.length !== 6) {
      toast.error('Please enter a 6-digit code');
      return;
    }
    
    setProcessing(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/auth/2fa/verify`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: verificationCode }),
      });
      
      if (!response.ok) throw new Error('Invalid code');
      
      setTwoFactorEnabled(true);
      setSetupData(null);
      setVerificationCode('');
      toast.success('Two-factor authentication enabled!');
    } catch (error) {
      toast.error('Invalid verification code');
    } finally {
      setProcessing(false);
    }
  };

  const handleDisable2FA = async () => {
    if (verificationCode.length !== 6) {
      toast.error('Please enter your current 2FA code');
      return;
    }
    
    setProcessing(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/auth/2fa/disable`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: verificationCode }),
      });
      
      if (!response.ok) throw new Error('Invalid code');
      
      setTwoFactorEnabled(false);
      setVerificationCode('');
      toast.success('Two-factor authentication disabled');
    } catch (error) {
      toast.error('Invalid verification code');
    } finally {
      setProcessing(false);
    }
  };

  const handleRevokeAllSessions = async () => {
    if (!confirm('This will log you out of all devices. Continue?')) return;
    
    setProcessing(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/auth/sessions/all`, {
        method: 'DELETE',
        credentials: 'include',
      });
      
      if (response.ok) {
        toast.success('All sessions revoked');
        window.location.href = '/login';
      }
    } catch (error) {
      toast.error('Failed to revoke sessions');
    } finally {
      setProcessing(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 2FA Section */}
      <Card className="bg-gray-900/50 border-gray-800">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white">
            <Shield className="w-5 h-5 text-cyan-400" />
            Two-Factor Authentication
            {twoFactorEnabled ? (
              <Badge className="ml-2 bg-emerald-500/20 text-emerald-400">Enabled</Badge>
            ) : (
              <Badge variant="outline" className="ml-2 text-yellow-400 border-yellow-400/30">Not Enabled</Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {!twoFactorEnabled && !setupData && (
            <div>
              <p className="text-gray-400 mb-4">
                Add an extra layer of security to your account by enabling two-factor authentication.
              </p>
              <Button onClick={handleSetup2FA} disabled={processing}>
                {processing ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Smartphone className="w-4 h-4 mr-2" />
                )}
                Setup 2FA
              </Button>
            </div>
          )}

          {setupData && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-4"
            >
              <div className="flex flex-col md:flex-row gap-6">
                {/* QR Code */}
                <div className="flex-shrink-0">
                  <p className="text-sm text-gray-400 mb-2">1. Scan with authenticator app:</p>
                  <div className="bg-white p-2 rounded-lg w-fit">
                    <img src={setupData.qr_code} alt="2FA QR Code" className="w-40 h-40" />
                  </div>
                </div>

                {/* Manual Entry */}
                <div className="flex-1 space-y-4">
                  <div>
                    <p className="text-sm text-gray-400 mb-2">Or enter manually:</p>
                    <div className="flex items-center gap-2">
                      <code className="flex-1 p-3 bg-gray-800 rounded-lg text-sm text-cyan-400 font-mono">
                        {setupData.secret}
                      </code>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard(setupData.secret)}
                      >
                        <Copy className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>

                  {/* Backup Codes */}
                  <div>
                    <button
                      onClick={() => setShowBackupCodes(!showBackupCodes)}
                      className="flex items-center gap-2 text-sm text-gray-400 hover:text-gray-300"
                    >
                      {showBackupCodes ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      {showBackupCodes ? 'Hide' : 'Show'} backup codes
                    </button>
                    {showBackupCodes && (
                      <div className="mt-2 p-3 bg-gray-800 rounded-lg">
                        <p className="text-xs text-gray-500 mb-2">Save these codes securely:</p>
                        <div className="grid grid-cols-2 gap-2">
                          {setupData.backup_codes.map((code, i) => (
                            <code key={i} className="text-sm text-amber-400 font-mono">{code}</code>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Verification */}
              <div className="pt-4 border-t border-gray-800">
                <p className="text-sm text-gray-400 mb-2">2. Enter verification code:</p>
                <div className="flex items-center gap-2">
                  <Input
                    type="text"
                    maxLength={6}
                    value={verificationCode}
                    onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, ''))}
                    placeholder="000000"
                    className="w-32 text-center font-mono text-lg tracking-widest bg-gray-800 border-gray-700"
                  />
                  <Button onClick={handleVerify2FA} disabled={processing}>
                    {processing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4 mr-2" />}
                    Verify & Enable
                  </Button>
                  <Button variant="ghost" onClick={() => setSetupData(null)}>
                    Cancel
                  </Button>
                </div>
              </div>
            </motion.div>
          )}

          {twoFactorEnabled && !setupData && (
            <div>
              <p className="text-gray-400 mb-4">
                Two-factor authentication is active. Enter your current code to disable.
              </p>
              <div className="flex items-center gap-2">
                <Input
                  type="text"
                  maxLength={6}
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, ''))}
                  placeholder="000000"
                  className="w-32 text-center font-mono text-lg tracking-widest bg-gray-800 border-gray-700"
                />
                <Button variant="destructive" onClick={handleDisable2FA} disabled={processing}>
                  {processing ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                  Disable 2FA
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Active Sessions */}
      <Card className="bg-gray-900/50 border-gray-800">
        <CardHeader>
          <CardTitle className="flex items-center justify-between text-white">
            <span className="flex items-center gap-2">
              <Key className="w-5 h-5 text-cyan-400" />
              Active Sessions
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={fetchSecurityStatus}
              className="text-gray-400"
            >
              <RefreshCw className="w-4 h-4" />
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {sessions.length === 0 ? (
            <p className="text-gray-500 text-center py-4">No active sessions found</p>
          ) : (
            <div className="space-y-3">
              {sessions.map((session, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg"
                >
                  <div>
                    <p className="text-white text-sm">Session</p>
                    <p className="text-gray-500 text-xs">
                      Created: {new Date(session.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <Badge variant="outline" className="text-emerald-400 border-emerald-400/30">
                    Active
                  </Badge>
                </div>
              ))}
            </div>
          )}

          <div className="mt-4 pt-4 border-t border-gray-800">
            <Button
              variant="destructive"
              onClick={handleRevokeAllSessions}
              disabled={processing}
              className="w-full"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Logout All Devices
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Security Tips */}
      <Card className="bg-amber-500/10 border-amber-500/20">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-medium text-amber-400 mb-1">Security Tips</h4>
              <ul className="text-sm text-gray-400 space-y-1">
                <li>• Enable 2FA for maximum account security</li>
                <li>• Never share your API keys or backup codes</li>
                <li>• Regularly review your active sessions</li>
                <li>• Use a strong, unique password</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SecuritySettings;
