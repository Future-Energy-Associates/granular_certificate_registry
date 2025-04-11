import { createSlice } from "@reduxjs/toolkit";
import { login, logout } from "./authThunk";

const authSlice = createSlice({
  name: "auth",
  initialState: {
    user: null,
    userID: null,
    loading: false,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (state) => {
        state.loading = true;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload;
        state.userID = action.payload;
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        state.user = null;
        state.userID = null;
      })
      .addCase(logout.fulfilled, (state) => {
        state.user = null;
        state.userID = null;
      });
  },
});

export default authSlice.reducer;
