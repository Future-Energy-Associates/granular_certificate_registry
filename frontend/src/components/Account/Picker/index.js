import React from "react";
import { Typography, Space, Divider } from "antd";
import * as styles from "./AccountPicker.module.css";
import addUserBtn from "../../../assets/images/add-user-btn.png";
import { useNavigate } from "react-router-dom";
import { useDispatch } from "react-redux";
import { useAccount } from "../../../context/AccountContext";
import { getAccountDetails } from "../../../store/account/accountThunk";
import Cookies from "js-cookie";

const { Title, Text } = Typography;

const AccountPicker = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const userData = JSON.parse(Cookies.get("user_data"));
  const { saveAccountDetail } = useAccount();

  const handleAccountSelection = async (account) => {
    try {
      const accountDetail = await dispatch(
        getAccountDetails(account.id)
      ).unwrap();
      saveAccountDetail(accountDetail);
      navigate("/certificates");
    } catch (error) {
      console.error("Error selecting account:", error);
    }
  };

  const handleRequestAccount = () => {
    window.open(
      "https://docs.google.com/forms/d/e/1FAIpQLSdSkHMAYSu43VJFevngfVT5hvnWRZvwkelIf9QaPtpLVrIlxA/viewform?usp=sf_link",
      "_blank",
      "noopener,noreferrer"
    );
  };

  return (
    <div className={styles["account-picker-container"]}>
      <div className={styles["account-picker"]}>
        <div className={styles["header"]}>
          <Title level={3}>GranularCertOS</Title>
          <Text type="secondary">
            Choose an account to continue to GranularCertOS
          </Text>
        </div>

        {/* Map through user's accounts */}
        {userData?.accounts?.map((account, index) => (
          <React.Fragment key={account.id}>
            <div
              className={styles["account-card"]}
              onClick={() => handleAccountSelection(account)}
            >
              <Space>
                <div className={styles["account-initial"]}>
                  {account.account_name.charAt(0).toUpperCase()}
                </div>
                <div>
                  <Text style={{ display: "flex" }} strong>
                    {account.account_name}
                  </Text>
                </div>
              </Space>
            </div>
            {index < userData.accounts.length - 1 && (
              <Divider className={styles["account-card-divider"]} />
            )}
          </React.Fragment>
        ))}

        {/* Request Account Card */}
        <Divider className={styles["account-card-divider"]} />
        <div className={styles["account-card"]} onClick={handleRequestAccount}>
          <Space>
            <img
              src={addUserBtn}
              alt="Request Account"
              className={styles["logo-img"]}
            />
            <Text strong>Request another account</Text>
          </Space>
        </div>
      </div>
    </div>
  );
};

export default AccountPicker;
