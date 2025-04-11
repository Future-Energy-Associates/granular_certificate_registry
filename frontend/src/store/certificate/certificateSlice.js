import { createSlice } from "@reduxjs/toolkit";
import {
  fetchCertificates,
  transferCertificates,
  cancelCertificates,
} from "./certificateThunk";

const certificateSlice = createSlice({
  name: "certificates",
  initialState: {
    certificates: [],
    loading: false,
    error: null,
    lastFetch: null,
  },
  reducers: {
    clearErrors: (state) => {
      state.error = null;
    },
    clearCertificates: (state) => {
      state.certificates = [];
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchCertificates.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchCertificates.fulfilled, (state, action) => {
        state.loading = false;
        state.error = null;
        state.certificates = action.payload.granular_certificate_bundles || [];
        state.lastFetch = new Date().toISOString();
      })
      .addCase(fetchCertificates.rejected, (state, action) => {
        state.loading = false;
        state.certificates = [];
        state.error = {
          message: action.payload?.message || "Failed to fetch certificates",
          status: action.payload?.status,
          data: action.payload?.data,
        };
      })

      // Transfer certificates
      .addCase(transferCertificates.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(transferCertificates.fulfilled, (state, action) => {
        state.loading = false;
        state.error = null;
      })
      .addCase(transferCertificates.rejected, (state, action) => {
        state.loading = false;
        state.error = {
          message: action.payload?.message || "Failed to transfer certificates",
          status: action.payload?.status,
          data: action.payload?.data,
        };
      })

      // Cancel certificates
      .addCase(cancelCertificates.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(cancelCertificates.fulfilled, (state, action) => {
        state.loading = false;
        state.error = null;
      })
      .addCase(cancelCertificates.rejected, (state, action) => {
        state.loading = false;
        state.error = {
          message: action.payload?.message || "Failed to cancel certificates",
          status: action.payload?.status,
          data: action.payload?.data,
        };
      });
  },
});

export const { clearErrors, clearCertificates } = certificateSlice.actions;
export default certificateSlice.reducer;
