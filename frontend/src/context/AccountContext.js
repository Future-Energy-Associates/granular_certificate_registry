import React, { createContext, useContext, useEffect, useState } from "react";
import { saveDataToSessionStorage, getSessionStorage } from "../utils";

const AccountContext = createContext();

export const AccountProvider = ({ children }) => {
  const [currentAccount, setCurrentAccount] = useState(null);

  useEffect(() => {
    const accountDetail = getSessionStorage("account_detail");
    const accountSummary = getSessionStorage("account_summary");

    if (!!accountDetail && !!accountSummary) {
      const currentAccount = {
        detail: JSON.parse(accountDetail),
        summary: JSON.parse(accountSummary),
      };
      try {
        setCurrentAccount(currentAccount);
      } catch (err) {
        console.log(err);
      }
    }
  }, []);

  const saveAccountDetail = ({ detail, summary }) => {
    setCurrentAccount({ detail, summary });
    // Save the object to sessionStorage as a string
    saveDataToSessionStorage("account_detail", JSON.stringify(detail));
    saveDataToSessionStorage("account_summary", JSON.stringify(summary));
  };

  return (
    <AccountContext.Provider value={{ currentAccount, saveAccountDetail }}>
      {children}
    </AccountContext.Provider>
  );
};

export const useAccount = () => useContext(AccountContext);
