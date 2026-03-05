import React from 'react';
import { Auth0Provider, useAuth0 } from '@auth0/auth0-react';
import Dashboard from './components/Dashboard';
import Login from './components/Login';
import { AUTH0_DOMAIN, AUTH0_CLIENT_ID } from './config';
import './index.css';

function AppContent() {
  const { isAuthenticated, isLoading, error, getAccessTokenSilently, getIdTokenClaims } = useAuth0();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0f0f23] flex items-center justify-center">
        <div className="text-slate-400">Loading...</div>
      </div>
    );
  }

  if (error) {
    console.error('Auth0 error:', error);
  }

  if (!isAuthenticated) {
    return <Login />;
  }

  // Use getIdTokenClaims as fallback when no audience is configured
  const getToken = async () => {
    try {
      return await getAccessTokenSilently();
    } catch {
      // When no audience is set, use the ID token instead
      const claims = await getIdTokenClaims();
      return claims?.__raw || '';
    }
  };

  return <Dashboard getAccessToken={getToken} />;
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
      }}
      cacheLocation="localstorage"
    >
      <AppContent />
    </Auth0Provider>
  );
}

export default App;
