// src/store/errorSlice.js
import { createSlice } from "@reduxjs/toolkit";

const errorSlice = createSlice({
  name: "error",
  initialState: { message: null, status: null },
  reducers: {
    setError: (state, action) => {
      console.log("Errors logged");
      state.message = action.payload.message;
      state.status = action.payload.status;
    },
    clearError: (state) => {
      console.log("Errors cleared");
      state.message = null;
      state.status = null;
    },
  },
});

export const { setError, clearError } = errorSlice.actions;
export default errorSlice.reducer;
