import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    // Set Accept-Language header based on browser locale
    config.headers["Accept-Language"] = navigator.language;
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

export default api;
