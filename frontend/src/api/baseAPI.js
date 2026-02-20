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

/**
 * Parse a structured error response from the API.
 * 
 * Expected API error format:
 * {
 *   status_code: number,
 *   error_type: "validation_error" | "http_error" | "server_error",
 *   error_message: string,
 *   details: {
 *     errors?: Array<{
 *       field: string,
 *       message: string,
 *       invalid_value: any,
 *       location: string,
 *       type: string
 *     }>,
 *     method?: string,
 *     path?: string,
 *     endpoint?: string,
 *     ...
 *   }
 * }
 * 
 * @param {Object} responseData - The error response data from the API
 * @returns {Object} Structured error object
 */
const parseErrorResponse = (responseData) => {
  // Handle new structured error format
  if (responseData?.error_type) {
    return {
      status: responseData.status_code,
      errorType: responseData.error_type,
      message: responseData.error_message || "An error occurred",
      errors: responseData.details?.errors || [],
      details: responseData.details || {},
      isValidationError: responseData.error_type === "validation_error",
    };
  }

  // Handle legacy format (detail field)
  if (responseData?.detail) {
    return {
      status: responseData.status_code || 500,
      errorType: "unknown",
      message: typeof responseData.detail === "string" 
        ? responseData.detail 
        : "An error occurred",
      errors: [],
      details: {},
      isValidationError: false,
    };
  }

  // Fallback for unexpected formats
  return {
    status: 500,
    errorType: "unknown",
    message: "An unexpected error occurred",
    errors: [],
    details: {},
    isValidationError: false,
  };
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
    console.error("API Error:", error);

    // Check for a network error
    if (
      (error.code === "ERR_NETWORK" || !error.response) &&
      window.location.pathname !== "/login"
    ) {
      // Redirect to login on network error
      window.location.href = "/login";
      return Promise.reject({
        status: 0,
        errorType: "network_error",
        message: "Network error - please check your connection",
        errors: [],
        details: {},
        isValidationError: false,
      });
    }

    // Handle CSRF token refresh
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

    // Parse the structured error response
    const parsedError = parseErrorResponse(error.response?.data);
    
    // Override status from response if available
    if (error.response?.status) {
      parsedError.status = error.response.status;
    }

    return Promise.reject(parsedError);
  }
);

fetchCSRFToken().catch(console.error);

export default baseAPI;
export { parseErrorResponse };