// API Configuration
// In production, use relative URLs to go through Nginx proxy
// In development, connect directly to backend

const getApiBaseUrl = () => {
  // If running in production (accessed via domain or IP), use relative URLs
  if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    return ''; // Use relative URLs - will be proxied by Nginx
  }
  
  // In development, connect directly to backend
  return 'http://localhost:8080';
};

export const API_BASE_URL = getApiBaseUrl();

// Helper function to construct full API URLs
export const getApiUrl = (path) => {
  // Ensure path starts with /api/
  const apiPath = path.startsWith('/api/') ? path : `/api/${path.replace(/^\//, '')}`;
  return `${API_BASE_URL}${apiPath}`;
};

export default {
  API_BASE_URL,
  getApiUrl
};
