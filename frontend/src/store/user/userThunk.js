import { createAsyncThunk } from "@reduxjs/toolkit";
import { readUserAPI, readCurrentUserAPI } from "../../api/userAPI";
import { saveDataToCookies } from "../../utils";

export const readUser = createAsyncThunk(
  "user/readUser",
  async (userID, { rejectWithValue }) => {
    try {
      const response = await readUserAPI(userID);
      const userData = {
        accounts: response?.data?.accounts || [],
        userInfo: {
          username: response?.data?.username,
          role: response?.data?.role,
          userID: userID,
          organisation: response?.data?.organisation,
          email: response?.data?.email,
        },
      };

      saveDataToCookies("user_data", JSON.stringify(userData));

      return userData;
    } catch (error) {
      return rejectWithValue(error.response.data);
    }
  }
);

export const readCurrentUser = createAsyncThunk(
  "user/readCurrentUser",
  async (_, { rejectWithValue }) => {
    try {
      const response = await readCurrentUserAPI();

      const userData = {
        accounts: response?.data?.accounts || [],
        userInfo: {
          username: response?.data?.name,
          role: response?.data?.role,
          userID: response?.data?.id,
          organisation: response?.data?.organisation,
          email: response?.data?.email,
        },
      };

      saveDataToCookies("user_data", JSON.stringify(userData));

      return userData;
    } catch ({ message, status }) {
      return rejectWithValue({ message, status });
    }
  }
);
