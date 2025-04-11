import { createSlice } from "@reduxjs/toolkit";
import { readUser, readCurrentUser } from "./userThunk";

const userSlice = createSlice({
  name: "user",
  initialState: {
    accounts: [],
    selectedAccount: null,
    userInfo: {
      username: null,
      role: null,
      userID: null,
      organisation: null,
      email: null,
    },
    loading: false,
    error: null,
  },
  reducers: {
    clearUser: (state) => {
      state.accounts = [];
      state.selectedAccount = null;
      state.userInfo = {
        username: null,
        role: null,
        userID: null,
        organisation: null,
        email: null,
      };
      state.error = null;
    },
    setCurrentUserInfoState: (state, action) => {
      state.userInfo = {
        username: action.payload.userInfo.username,
        role: action.payload.userInfo.role,
        userID: action.payload.userInfo.userID,
        organisation: action.payload.userInfo.organisation,
        email: action.payload.userInfo.email,
      };
    },
    setSelectedAccount: (state, action) => {
      state.selectedAccount = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(readUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(readUser.fulfilled, (state, action) => {
        state.loading = false;
        state.accounts = action.payload.accounts;
        state.userInfo = action.payload.userInfo;
        if (action.payload.accounts.length > 0) {
          state.selectedAccount = action.payload.accounts[0];
        }
      })
      .addCase(readUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
        state.accounts = [];
        state.selectedAccount = null;
        state.userInfo = {
          username: null,
          role: null,
          userID: null,
        };
      })
      .addCase(readCurrentUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(readCurrentUser.fulfilled, (state, action) => {
        state.loading = false;
        state.accounts = action.payload.accounts;
        state.userInfo = action.payload.userInfo;
        if (action.payload.accounts.length > 0) {
          state.selectedAccount = action.payload.accounts[0];
        }
      })
      .addCase(readCurrentUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
        state.accounts = [];
        state.selectedAccount = null;
        state.userInfo = {
          username: null,
          role: null,
          userID: null,
        };
      });
  },
});

export const { clearUser, setSelectedAccount, setCurrentUserInfoState } =
  userSlice.actions;
export default userSlice.reducer;
