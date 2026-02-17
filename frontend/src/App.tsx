import React, { useState, useEffect } from 'react';
import { Auth0Provider, useAuth0 } from '@auth0/auth0-react';
import Dashboard from './components/Dashboard';
import Login from './components/Login';
import { AUTH0_DOMAIN, AUTH0_CLIENT_ID, AUTH0_AUDIENCE } from './config';
import './index.css';

function AppContent() {
  const { isAuthenticated, isLoading, getAccessTokenSilently } = useAuth0();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0f0f23] flex items-center justify-center">
        <div className="text-slate-400">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Login />;
  }

  return <Dashboard getAccessToken={getAccessTokenSilently} />;
}

function App() {
  if (!AUTH0_DOMAIN || !AUTH0_CLIENT_ID) {
    return (
      <div className="min-h-screen bg-[#0f0f23] flex items-center justify-center">
        <div className="text-red-400 text-center max-w-md p-6">
          <h2 className="text-xl font-bold mb-2">Auth0 Not Configured</h2>
          <p className="text-sm text-slate-400">
            Set VITE_AUTH0_DOMAIN and VITE_AUTH0_CLIENT_ID in your frontend .env file.
          </p>
        </div>
      </div>
    );
  }

  return (
    <Auth0Provider
      domain={AUTH0_DOMAIN}
      clientId={AUTH0_CLIENT_ID}
      authorizationParams={{
        redirect_uri: window.location.origin,
        audience: AUTH0_AUDIENCE,
      }}
    >
      <AppContent />
    </Auth0Provider>
  );
}

export default App;
