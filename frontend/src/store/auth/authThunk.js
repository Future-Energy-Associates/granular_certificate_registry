import { createAsyncThunk } from "@reduxjs/toolkit";
import { loginAPI } from "../../api/authAPI";
import { setError, clearError } from "../error/errorSlice";
import Cookies from "js-cookie";

// Save token to cookie
const saveTokenToCookie = (access_token) => {
  Cookies.set("access_token", access_token, {
    expires: 7,
    path: "",
    secure: true,
  });
};

// Remove token from cookie
const removeTokenFromCookie = () => {
  Cookies.remove("access_token");
};

// Login thunk
export const login = createAsyncThunk(
  "auth/login",
  async (credentials, { dispatch, rejectWithValue }) => {
    try {
      dispatch(clearError()); // Clear previous errors
      const response = await loginAPI(credentials);
      const { access_token, token_type, user_id } = response?.data;

      if (!access_token) {
        throw new Error("No access token received.");
      }

      saveTokenToCookie(access_token);

      return user_id;
    } catch (error) {
      const status = error.status || 500;
      const message = error.message || "Login failed. Please try again.";

      dispatch(setError({ status: status, message: message })); // Store error in state

      return rejectWithValue(message); // Pass error to rejected state
    }
  }
);

// Logout thunk
export const logout = createAsyncThunk("auth/logout", async () => {
  removeTokenFromCookie();
});
