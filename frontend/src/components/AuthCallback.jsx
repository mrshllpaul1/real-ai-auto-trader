/**
 * AuthCallback - Handles OAuth callback from Emergent Google Auth
 * Processes session_id from URL fragment and exchanges for user data
 */

import React, { useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Loader2 } from 'lucide-react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL || '';

const AuthCallback = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const hasProcessed = useRef(false);

  useEffect(() => {
    // Prevent double processing in StrictMode
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processAuth = async () => {
      try {
        // Extract session_id from URL fragment
        const hash = window.location.hash;
        const params = new URLSearchParams(hash.substring(1));
        const sessionId = params.get('session_id');

        if (!sessionId) {
          console.error('No session_id in URL');
          navigate('/login', { replace: true });
          return;
        }

        // Exchange session_id for user data
        const response = await fetch(`${BACKEND_URL}/api/auth/session`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ session_id: sessionId })
        });

        if (!response.ok) {
          throw new Error('Failed to exchange session');
        }

        const userData = await response.json();

        // Store user data in localStorage for quick access
        localStorage.setItem('user_id', userData.user_id);
        localStorage.setItem('user_name', userData.name);
        localStorage.setItem('user_email', userData.email);
        localStorage.setItem('authenticated', 'true');

        // Clear URL fragment
        window.history.replaceState(null, '', window.location.pathname);

        // Check if onboarding needed
        if (!userData.onboarding_completed) {
          navigate('/', { replace: true, state: { user: userData, showOnboarding: true } });
        } else {
          navigate('/', { replace: true, state: { user: userData } });
        }
      } catch (error) {
        console.error('Auth callback error:', error);
        localStorage.removeItem('authenticated');
        navigate('/login', { replace: true });
      }
    };

    processAuth();
  }, [navigate]);

  return (
    <div className="min-h-screen bg-[#0A0A0A] flex items-center justify-center">
      <div className="text-center">
        <Loader2 className="w-12 h-12 text-cyan-400 animate-spin mx-auto mb-4" />
        <p className="text-gray-400">Signing you in...</p>
      </div>
    </div>
  );
};

export default AuthCallback;
