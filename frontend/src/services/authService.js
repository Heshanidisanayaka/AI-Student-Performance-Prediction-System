import api from './api';

export const authService = {
  async login(email, password) {
    const response = await api.post('/auth/login', { email, password });
    const { access_token, user } = response.data;
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('user', JSON.stringify(user));
    return { token: access_token, user };
  },

  async register(userData) {
    const response = await api.post('/auth/register', userData);
    const { access_token, user } = response.data;
    if (access_token) {
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('user', JSON.stringify(user));
    }
    return response.data;
  },

  async getCurrentUser() {
    const response = await api.get('/auth/me');
    localStorage.setItem('user', JSON.stringify(response.data));
    return response.data;
  },

  async logout() {
    try {
      await api.post('/auth/logout');
    } catch {
      // Ignore network failures on logout
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
    }
  },

  getStoredUser() {
    try {
      const data = localStorage.getItem('user');
      return data ? JSON.parse(data) : null;
    } catch {
      return null;
    }
  },

  getStoredToken() {
    return localStorage.getItem('access_token');
  },

  setSession(token, user) {
    localStorage.setItem('access_token', token);
    localStorage.setItem('user', JSON.stringify(user));
  },
};
