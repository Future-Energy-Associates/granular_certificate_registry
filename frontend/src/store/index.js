import { configureStore } from "@reduxjs/toolkit";
import authReducer from "./auth/authSlice";
import certificateReducer from "./certificate/certificateSlice";
import accountReducer from "./account/accountSlice";
import userReducer from "./user/userSlice";
import errorReducer from "./error/errorSlice";

export const store = configureStore({
  reducer: {
    auth: authReducer, // Auth state
    certificates: certificateReducer, // Certificate state
    account: accountReducer, // Account state
    user: userReducer, // User state
    error: errorReducer, // Error state
  },
});
