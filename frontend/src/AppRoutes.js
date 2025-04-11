import React, { useEffect } from "react";
import Cookies from "js-cookie";

// Import pages
const Login = React.lazy(() => import("./pages/Login"));

const Main = React.lazy(() => import("./pages/Main"));

const Certificate = React.lazy(() => import("./components/certificate"));

const Device = React.lazy(() => import("./components/device"));

// const Transfer = React.lazy(() => import("./components/Transfer"));

const AccountPicker = React.lazy(() => import("./components/account/Picker"));

const AccountManagement = React.lazy(() =>
  import("./components/account/Management")
);

import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useNavigate,
  useLocation,
} from "react-router-dom";

import { message } from "antd";

import { useDispatch } from "react-redux";
import { readCurrentUser } from "./store/user/userThunk";
import { useUser } from "./context/UserContext";

const isAuthenticated = () => {
  const token = Cookies.get("access_token");
  return !!token;
};

const PrivateRoute = ({ element: Element, ...rest }) => {
  return isAuthenticated() ? <Element {...rest} /> : <Navigate to="/login" />;
};

const AppRoutes = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { saveUserData } = useUser();

  useEffect(() => {
    const validateCredentials = async () => {
      try {
        const userData = await dispatch(readCurrentUser()).unwrap();
        saveUserData(userData);
      } catch (err) {
        console.error("Failed to validate credentials:", err);
        message.error(err?.message || "Credentials validation failed", 3);
        navigate("/login");
      }
    };

    if (location.pathname !== "/login") {
      validateCredentials();
    }
  }, [dispatch]);

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/account-picker"
        element={<PrivateRoute element={AccountPicker} />}
      />
      <Route path="/" element={<Main />}>
        <Route index element={<Navigate to="/certificates" replace />} />
        {/* <Route path="/" element={<Navigate to="/certificates" />} /> */}
        <Route
          path="/certificates"
          element={<PrivateRoute element={Certificate} />}
        />
        <Route path="/devices" element={<PrivateRoute element={Device} />} />
        {/* <Route
            path="/transfer-history"
            element={<PrivateRoute element={Transfer} />}
          /> */}
        <Route
          path="/account-management"
          element={<PrivateRoute element={AccountManagement} />}
        />
        {/* Catch-all route */}
        <Route path="*" element={<Navigate to="/certificates" replace />} />
      </Route>
    </Routes>
  );
};

export default AppRoutes;
