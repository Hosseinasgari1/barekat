import axios from 'axios';
import { store } from '../store';
import { logout, setCredentials } from '../features/auth/authSlice';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Automatically attach access token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response Interceptor: Handle token expiration and auto-refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // If error is 401 and we haven't retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');

      if (refreshToken) {
        try {
          // Attempt to refresh the access token
          const apiURL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/';
          const response = await axios.post(`${apiURL}token/refresh/`, {
            refresh: refreshToken,
          });

          const newAccessToken = response.data.access;
          const newRefreshToken = response.data.refresh || refreshToken;

          // Save credentials in store and localStorage
          store.dispatch(
            setCredentials({
              accessToken: newAccessToken,
              refreshToken: newRefreshToken,
            })
          );

          // Retry the original request with the new access token
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          return api(originalRequest);
        } catch (refreshError) {
          // If refresh fails, log out the user
          store.dispatch(logout());
          return Promise.reject(refreshError);
        }
      } else {
        store.dispatch(logout());
      }
    }
    return Promise.reject(error);
  }
);

export default api;
