import axios from "axios";
import Cookies from "js-cookie";

const AUTH_LIST = ["/auth/login"];
const CSRF_EXEMPT = ["/csrf-token"];

const baseAPI = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});

const fetchCSRFToken = async () => {
  try {
    const response = await baseAPI.get("/csrf-token");
    return response.data.csrf_token;
  } catch (error) {
    console.error("Failed to fetch CSRF token:", error);
    return null;
  }
};

baseAPI.interceptors.request.use(
  async (config) => {
    const isAuthRoute = AUTH_LIST.some((route) => config.url?.includes(route));
    const isCSRFExempt = CSRF_EXEMPT.some((route) =>
      config.url?.includes(route)
    );

    if (!isAuthRoute) {
      const token = Cookies.get("access_token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }

    if (!isCSRFExempt && config.method !== "get") {
      const csrfToken = await fetchCSRFToken();
      if (csrfToken) {
        config.headers["X-CSRF-Token"] = csrfToken;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

baseAPI.interceptors.response.use(
  (response) => response,
  async (error) => {
    console.error(error);

    // Check for a network error
    if (
      (error.code === "ERR_NETWORK" || !error.response) &&
      window.location.pathname !== "/login"
    ) {
      // Redirect to login on network error
      window.location.href = "/login";
      return Promise.reject(error);
    }

    if (
      error.response?.status === 403 &&
      error.response?.data?.detail?.includes("CSRF")
    ) {
      const newToken = await fetchCSRFToken();
      if (newToken && error.config) {
        error.config.headers["X-CSRF-Token"] = newToken;
        return baseAPI(error.config);
      }
    }

    const status = error.response?.status || 500;
    const message =
      error.response?.data?.detail || "An unexpected error occurred.";

    return Promise.reject({ status, message });
  }
);

fetchCSRFToken().catch(console.error);

export default baseAPI;
