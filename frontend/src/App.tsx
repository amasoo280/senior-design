import React, { useState, useEffect } from 'react';
<<<<<<< HEAD
import { GoogleOAuthProvider } from '@react-oauth/google';
import Dashboard from './components/Dashboard';
import Login from './components/Login';
import { verifyAuth, isAuthenticated } from './utils/auth';
import { GOOGLE_CLIENT_ID, AUTH_TOKEN_KEY } from './config';
=======
import Dashboard from './components/Dashboard';
import Login from './components/Login';
import { verifyAuth, isAuthenticated } from './utils/auth';
>>>>>>> 078316479d1a2862d1e450732b847d276ddee3e9
import './index.css';

function App() {
  const [isAuthenticatedState, setIsAuthenticatedState] = useState<boolean>(false);
  const [isCheckingAuth, setIsCheckingAuth] = useState<boolean>(true);

  useEffect(() => {
    const checkAuth = async () => {
      if (isAuthenticated()) {
        const isValid = await verifyAuth();
        setIsAuthenticatedState(isValid);
        if (!isValid) {
          // Token is invalid, clear it
<<<<<<< HEAD
          localStorage.removeItem(AUTH_TOKEN_KEY);
=======
          localStorage.removeItem('sargon_auth_token');
>>>>>>> 078316479d1a2862d1e450732b847d276ddee3e9
        }
      }
      setIsCheckingAuth(false);
    };

    checkAuth();
  }, []);

  const handleLoginSuccess = () => {
    setIsAuthenticatedState(true);
  };

  const handleLogout = () => {
    setIsAuthenticatedState(false);
  };

  if (isCheckingAuth) {
    return (
      <div className="min-h-screen bg-[#0f0f23] flex items-center justify-center">
        <div className="text-slate-400">Loading...</div>
      </div>
    );
  }

<<<<<<< HEAD
  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      {!isAuthenticatedState ? (
        <Login onLoginSuccess={handleLoginSuccess} />
      ) : (
        <Dashboard onLogout={handleLogout} />
      )}
    </GoogleOAuthProvider>
  );
=======
  if (!isAuthenticatedState) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  return <Dashboard onLogout={handleLogout} />;
>>>>>>> 078316479d1a2862d1e450732b847d276ddee3e9
}

export default App;
