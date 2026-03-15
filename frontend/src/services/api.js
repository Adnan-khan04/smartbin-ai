import config from '../config';

// API Service for all backend communication
class APIService {
  constructor() {
    this.baseURL = config.api.baseURL;
    this.timeout = config.api.timeout;
  }

  // Helper method for making API calls
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const token = localStorage.getItem('token');

    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        throw {
          status: response.status,
          message: data?.detail || data?.message || `HTTP ${response.status}`,
          data,
        };
      }

      return data;
    } catch (error) {
      if (error.name === 'AbortError') {
        throw new Error('Request timeout - server not responding');
      }
      if (error.status === 401) {
        // Clear token if unauthorized
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
      throw error;
    }
  }

  // Auth endpoints
  async register(username, password, email = null) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password, email }),
    });
  }

  async login(username, password) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
  }

  async me() {
    return this.request('/auth/me', { method: 'GET' });
  }

  // Classification endpoints
  async classifyImage(file) {
    const formData = new FormData();
    formData.append('file', file);

    const token = localStorage.getItem('token');
    const headers = {};

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    try {
      const response = await fetch(`${this.baseURL}/classify/image`, {
        method: 'POST',
        headers,
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Classification failed: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      throw error;
    }
  }

  async confirmClassification(wasteType, confidence, probabilities) {
    return this.request('/classify/confirm', {
      method: 'POST',
      body: JSON.stringify({
        waste_type: wasteType,
        confidence,
        probabilities,
      }),
    });
  }

  // Gamification endpoints
  async getUserStats(userId) {
    return this.request(`/gamification/stats/${userId}`, { method: 'GET' });
  }

  async getLeaderboard() {
    return this.request('/gamification/leaderboard', { method: 'GET' });
  }

  // Dashboard endpoints
  async getDashboard() {
    return this.request('/dashboard', { method: 'GET' });
  }


}

export default new APIService();
