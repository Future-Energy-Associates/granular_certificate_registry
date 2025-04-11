import { createSlice } from "@reduxjs/toolkit";
import { createDevice } from "./deviceThunk";

const deviceSlice = createSlice({
  name: "devices",
  initialState: {
    devices: [],
    loading: false,
    uploadingMeterData: false,
    error: null,
  },
  reducers: {
    setUploadingMeterData: (state, action) => {
      state.uploadingMeterData = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(createDevice.pending, (state) => {
        state.loading = true;
      })
      .addCase(createDevice.fulfilled, (state, action) => {
        state.loading = false;
        state.devices = action.payload;
      })
      .addCase(createDevice.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      });
  },
});

export const { setUploadingMeterData } = deviceSlice.actions;
export default deviceSlice.reducer;
