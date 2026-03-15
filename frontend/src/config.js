// Frontend environment configuration
// This file centralizes API endpoints and environment-specific settings

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';
const APP_ENV = import.meta.env.MODE || 'development';

export const config = {
  api: {
    baseURL: API_BASE_URL,
    authEndpoint: `${API_BASE_URL}/auth`,
    classifyEndpoint: `${API_BASE_URL}/classify`,
    gamificationEndpoint: `${API_BASE_URL}/gamification`,
    dashboardEndpoint: `${API_BASE_URL}/dashboard`,
    timeout: 30000, // 30 seconds
  },
  app: {
    name: import.meta.env.VITE_APP_NAME || 'SmartBin AI',
    environment: APP_ENV,
    isDevelopment: APP_ENV === 'development',
    isProduction: APP_ENV === 'production',
  },
  features: {
    enableGamification: true,
    enableLeaderboard: true,
    enableDebugMode: APP_ENV === 'development',
  },
};

// Validate critical configuration
if (!config.api.baseURL) {
  console.error('ERROR: VITE_API_URL not configured');
}

export default config;
