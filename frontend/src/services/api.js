import axios from 'axios';

const API_URL = 'http://127.0.0.1:8086';

const api = axios.create({
  baseURL: API_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authAPI = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (data) => api.post('/auth/register', data),
  getMe: () => api.get('/auth/me'),
  refresh: (refresh_token) => api.post('/auth/refresh', { refresh_token }),
};

export const dataAPI = {
  getReclamations: (page = 1, page_size = 10) => api.get('/get_reclamations', { params: { page, page_size } }),
  getDemandes: (page = 1, page_size = 10) => api.get('/get_demandes', { params: { page, page_size } }),
  getAll: (page = 1, page_size = 10) => api.get('/get_all', { params: { page, page_size } }),
};

export const pollerAPI = {
  start: (cooldown_seconds = 60) => api.post('/refresh/start', { cooldown_seconds }),
  stop: () => api.post('/refresh/stop'),
  getStatus: () => api.get('/refresh/status'),
  fetchOnce: () => api.post('/refresh/once'),
};

export default api;
