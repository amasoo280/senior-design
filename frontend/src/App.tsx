import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import Login from './components/Login';
import { verifyAuth, isAuthenticated } from './utils/auth';
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
          localStorage.removeItem('sargon_auth_token');
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

  if (!isAuthenticatedState) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  return <Dashboard onLogout={handleLogout} />;
}

export default App;
