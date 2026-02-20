import baseAPI from "./baseAPI";

export const loginAPI = (credentials) => {
  return baseAPI.post("/auth/login", credentials, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
};

export const createApiKeyAPI = (payload) => {
  // payload: { name: string, expires_days?: number }
  return baseAPI.post("/auth/api-key", payload);
};

export const listApiKeysAPI = () => {
  return baseAPI.get("/auth/api-keys");
};

export const deactivateApiKeyAPI = (id) => {
  return baseAPI.delete(`/auth/api-key/${id}`);
};
