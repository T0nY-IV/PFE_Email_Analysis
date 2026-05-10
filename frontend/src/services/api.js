import axios from 'axios';

const API_URL = 'http://127.0.0.1:8086';
var Page_S = 24;

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
  changePassword: (data) => api.post('/auth/change-password', data),
  refresh: (refresh_token) => api.post('/auth/refresh', { refresh_token }),
  getUsers: (role) => api.get('/auth/users', role ? { params: { role } } : {}),
  createUser: (data) => api.post('/auth/users', data),
  updateUser: (userId, data) => api.put(`/auth/users/${userId}`, data),
  deleteUser: (userId) => api.delete(`/auth/users/${userId}`),
};

export const dataAPI = {
  getReclamations: (page = 1, page_size = 24, q = '') => api.get('/get_reclamations', { params: { page, page_size, q } }),
  getDemandes: (page = 1, page_size = 24, q = '') => api.get('/get_demandes', { params: { page, page_size, q } }),
  getAll: (page = 1, page_size = 24, q = '') => api.get('/get_all', { params: { page, page_size, q } }),
  getMonthlyStats: () => api.get('/stats/monthly'),
};

export const pollerAPI = {
  start: (cooldown_seconds = 60) => api.post('/refresh/start', { cooldown_seconds }),
  stop: () => api.post('/refresh/stop'),
  getStatus: () => api.get('/refresh/status'),
  fetchOnce: () => api.post('/refresh/once'),
};

export const reclamationsAPI = {
  markResolved: (email_uid) => api.post('/reclamations/mark-resolved', { email_uid }),
  markUnresolved: (email_uid) => api.delete(`/reclamations/mark-unresolved/${email_uid}`),
  isResolved: (email_uid) => api.get(`/reclamations/is-resolved/${email_uid}`),
  getResolvedList: () => api.get('/reclamations/resolved-list'),
};

export const demandesAPI = {
  markResolved: (email_uid) => api.post('/demandes/mark-resolved', { email_uid }),
  markUnresolved: (email_uid) => api.delete(`/demandes/mark-unresolved/${email_uid}`),
  isResolved: (email_uid) => api.get(`/demandes/is-resolved/${email_uid}`),
  getResolvedList: () => api.get('/demandes/resolved-list'),
};

let onSessionExpired = () => { };

export const setSessionExpiredHandler = (handler) => {
  onSessionExpired = handler;
};

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Check if it's not the login request itself
      if (!error.config.url.includes('/auth/login')) {
        onSessionExpired();
      }
    }
    return Promise.reject(error);
  }
);

export default api;
