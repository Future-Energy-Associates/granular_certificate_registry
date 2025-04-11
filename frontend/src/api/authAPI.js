import baseAPI from "./baseAPI";

export const loginAPI = (credentials) => {
  return baseAPI.post("/auth/login", credentials, {
    headers: {
      "Content-Type": "multipart/form-data", // Required for file uploads
    },
  });
};
