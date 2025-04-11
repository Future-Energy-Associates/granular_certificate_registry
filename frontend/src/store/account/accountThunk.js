import { createAsyncThunk } from "@reduxjs/toolkit";
import {
  getAccountAPI,
  getAccountSummaryAPI,
  getAccountDevicesAPI,
  getAccountWhitelistInverseAPI,
  getAccountCertificatesDevicesAPI,
} from "../../api/accountAPI";

// Thunk to fetch account details
export const getAccountDetails = createAsyncThunk(
  "account/getDetails",
  async (accountId, { rejectWithValue }) => {
    try {
      const [
        accountResponse,
        accountSummaryResponse,
        devicesResponse,
        certificatesDevicesResponse,
        whiteListResponse,
      ] = await Promise.all([
        getAccountAPI(accountId),
        getAccountSummaryAPI(accountId),
        getAccountDevicesAPI(accountId),
        getAccountCertificatesDevicesAPI(accountId),
        getAccountWhitelistInverseAPI(accountId),
      ]);

      const accountDetail = {
        detail: {
          ...accountResponse.data,
          devices: devicesResponse.data,
          certificateDevices: certificatesDevicesResponse.data,
          whiteListInverse: whiteListResponse.data,
        },
        summary: accountSummaryResponse.data,
      };
      return accountDetail;
    } catch (error) {
      console.error("Failed to fetch account details:", error);
      return rejectWithValue(error.response?.data || "An error occurred");
    }
  }
);
