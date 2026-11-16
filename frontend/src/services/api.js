import axios from 'axios';

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Request Interceptor: Attach JWT bearer token from localStorage
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Format error messages
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const errorData = error.response?.data;
    let message = 'An unexpected error occurred. Please try again.';

    if (errorData?.error?.message) {
      message = errorData.error.message;
    } else if (errorData?.detail) {
      if (Array.isArray(errorData.detail)) {
        message = errorData.detail.map((d) => d.msg || d.message).join(', ');
      } else {
        message = errorData.detail;
      }
    } else if (error.message) {
      message = error.message;
    }

    return Promise.reject(new Error(message));
  }
);

export default api;
