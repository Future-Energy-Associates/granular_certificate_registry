import React, { StrictMode } from "react";
import { Provider } from "react-redux";
import { BrowserRouter as Router } from "react-router-dom";
import { AccountProvider } from "./context/AccountContext";
import { UserProvider } from "./context/UserContext";
import { store } from "./store";
import AppRoutes from "./AppRoutes";

const App = () => {
  return (
    <Provider store={store}>
      <UserProvider>
        <AccountProvider>
          <StrictMode>
            <Router>
              <AppRoutes />
            </Router>
          </StrictMode>
        </AccountProvider>
      </UserProvider>
    </Provider>
  );
};

export default App;
