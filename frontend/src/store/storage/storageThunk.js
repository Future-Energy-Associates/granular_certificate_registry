import { createAsyncThunk } from "@reduxjs/toolkit";
import {
  getAllStorageRecordsForAccountAPI,
  getAllAllocatedStorageRecordsForAccountAPI,
} from "../../api/storageAPI";

export const fetchStorageRecords = createAsyncThunk(
  "storage/fetchStorageRecords",
  async (deviceIds, { rejectWithValue }) => {
    try {
      const response = await getAllStorageRecordsForAccountAPI(deviceIds);
      return response;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.detail || 
        error.message || 
        "Failed to fetch storage records"
      );
    }
  }
);

export const fetchAllocatedStorageRecords = createAsyncThunk(
  "storage/fetchAllocatedStorageRecords",
  async (deviceIds, { rejectWithValue }) => {
    try {
      const response = await getAllAllocatedStorageRecordsForAccountAPI(deviceIds);
      return response;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.detail || 
        error.message || 
        "Failed to fetch allocated storage records"
      );
    }
  }
); 