import { createSlice } from "@reduxjs/toolkit";
import { getAccountDetails } from "./accountThunk";

const accountSlice = createSlice({
  name: "account",
  initialState: {
    currentAccount: {
      id: null,
      account_name: "",
      devices: [],
      whiteListInverse: []
    },
    devices: [],
    loading: false,
    error: null,
  },
  reducers: {
    clearAccountState: (state) => {
      state.currentAccount = {
        id: null,
        account_name: "",
        devices: [],
      };
      state.error = null;
    },
    setAccountState: (state, action) => {
      state.currentAccount = action.payload
      state.devices = action.payload.devices
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(getAccountDetails.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getAccountDetails.fulfilled, (state, action) => {
        state.loading = false;
        state.currentAccount = {
          id: action.payload.id,
          account_name: action.payload.account_name,
          devices: action.payload.devices,
          whiteListInverse: action.payload.whiteListInverse
        };
        state.devices = action.payload.devices
      })
      .addCase(getAccountDetails.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
        state.currentAccount = {
          id: null,
          account_name: "",
          devices: [],
          whiteListInverse: []
        };
      });
  },
});

export const { clearAccountState, setAccountState } = accountSlice.actions;
export default accountSlice.reducer;
