import React, { createContext, useContext, useEffect, useState } from "react";
import { saveDataToSessionStorage, getSessionStorage } from "../utils";

const UserContext = createContext();

export const UserProvider = ({ children }) => {
  const [userData, setUserData] = useState(null);

  useEffect(() => {
    const userData = getSessionStorage("user_data");

    if (!!userData) {
      const parsedData = JSON.parse(userData);
      try {
        setUserData(parsedData);
      } catch (err) {
        console.log(err);
      }
    }
  }, []);

  const saveUserData = (userData) => {
    setUserData(userData);
    saveDataToSessionStorage("user_data", JSON.stringify(userData));
  };

  return (
    <UserContext.Provider value={{ userData, saveUserData }}>
      {children}
    </UserContext.Provider>
  );
};

export const useUser = () => useContext(UserContext);
