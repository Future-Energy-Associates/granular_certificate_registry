import { createSlice } from "@reduxjs/toolkit";
import {
  fetchStorageRecords,
  fetchAllocatedStorageRecords,
} from "./storageThunk";

const initialState = {
  storageRecords: [],
  allocatedStorageRecords: [],
  loading: false,
  error: null,
};

const storageSlice = createSlice({
  name: "storage",
  initialState,
  reducers: {
    clearStorageError: (state) => {
      state.error = null;
    },
    clearStorageData: (state) => {
      state.storageRecords = [];
      state.allocatedStorageRecords = [];
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch Storage Records
      .addCase(fetchStorageRecords.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchStorageRecords.fulfilled, (state, action) => {
        state.loading = false;
        state.storageRecords = action.payload;
        state.error = null;
      })
      .addCase(fetchStorageRecords.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Fetch Allocated Storage Records
      .addCase(fetchAllocatedStorageRecords.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchAllocatedStorageRecords.fulfilled, (state, action) => {
        state.loading = false;
        state.allocatedStorageRecords = action.payload;
        state.error = null;
      })
      .addCase(fetchAllocatedStorageRecords.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const { clearStorageError, clearStorageData } = storageSlice.actions;
export default storageSlice.reducer; 