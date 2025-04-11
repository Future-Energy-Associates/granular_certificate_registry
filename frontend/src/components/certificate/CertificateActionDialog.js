import React, { useState, forwardRef, useImperativeHandle } from "react";
import { Modal, Input, Select, Radio, message } from "antd";
import { useDispatch, useSelector } from "react-redux";
import { useAccount } from "../../context/AccountContext.js";
import {
  transferCertificates,
  cancelCertificates,
} from "../../store/certificate/certificateThunk.js";

const { Option } = Select;

const TransferCertificatesDialog = forwardRef((props, ref) => {
  const dispatch = useDispatch();

  const [visible, setVisible] = useState(false);
  const [transferType, setTransferType] = useState("percentage");
  const [percentage, setPercentage] = useState("");
  const [quantity, setQuantity] = useState("");
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [beneficiary, setBeneficiary] = useState("");
  const [accountError, setAccountError] = useState(false);

  const { userInfo } = useSelector((state) => state.user);

  const { currentAccount } = useAccount();
  // Expose methods to the parent component
  useImperativeHandle(ref, () => ({
    openDialog: () => setVisible(true),
    closeDialog: () => setVisible(false),
  }));

  const conditionalRendering = () => {
    switch (props.dialogAction) {
      case "cancel":
        return (
          <div style={{ marginTop: "24px", marginBottom: "48px" }}>
            <label>Beneficiary</label>
            <Input
              value={beneficiary}
              onChange={(e) => setBeneficiary(e.target.value)}
              style={{ width: "100%" }}
            />
          </div>
        );
        return;
      default:
        return (
          <div style={{ marginTop: "24px", marginBottom: "48px" }}>
            <label>
              Destination account <span style={{ color: "red" }}>*</span>
            </label>
            <Select
              value={selectedAccount}
              onChange={(value) => {
                setSelectedAccount(value);
                setAccountError(false);
              }}
              style={{
                width: "100%",
                borderColor: accountError ? "red" : undefined,
              }}
              status={accountError ? "error" : undefined}
            >
              {currentAccount?.detail.whiteListInverse.map((account) => (
                <Option value={account.id} key={account.id}>
                  {account.account_name}
                </Option>
              ))}{" "}
            </Select>
            {accountError && (
              <div style={{ color: "red", fontSize: "12px", marginTop: "4px" }}>
                Please select a destination account
              </div>
            )}
          </div>
        );
        return;
    }
  };

  const handleCancel = () => {
    setVisible(false);
    setAccountError(false);
    props.updateCertificateActionDialog(null);
  };

  const handleOk = async () => {
    // Check if destination account is selected for transfer action
    if (props.dialogAction !== "cancel" && !selectedAccount) {
      setAccountError(true);
      return;
    }

    // Parse the quantity and percentage values as float or return none
    const quantity_float_mwh = quantity ? parseFloat(quantity) : null;
    const percentage_float = percentage ? parseFloat(percentage) : null;

    if (
      parseFloat(percentage_float) < 0 ||
      parseFloat(percentage_float) > 100
    ) {
      message.error("Percentage must be between 0 and 100");
      return;
    }

    if (
      parseFloat(quantity_float_mwh) < 0 ||
      parseFloat(quantity_float_mwh) > props.totalProduction / 1e6
    ) {
      message.error(
        "Quantity must be more than 0 and less than total production: " +
          props.totalProduction / 1e6 +
          " MWh"
      );
      return;
    }

    if (quantity && percentage) {
      message.error(
        "Please specify either quantity or percentage, not both",
        3
      );
      return;
    }

    try {
      let apiBody = {
        source_id: currentAccount?.detail.id,
        user_id: userInfo.userID,
        granular_certificate_bundle_ids: props.selectedRowKeys,
        localise_time: true,
        action_type: props.dialogAction,
      };

      // if quanity not null add the quantity to the apiBody
      if (quantity_float_mwh) {
        apiBody = {
          ...apiBody,
          certificate_quantity: quantity_float_mwh * 1e6,
        };
      }

      // if percentage not null add the percentage to the apiBody
      if (percentage_float) {
        apiBody = {
          ...apiBody,
          certificate_bundle_percentage: percentage_float / 100,
        };
      }

      switch (props.dialogAction) {
        case "cancel":
          apiBody = { ...apiBody, beneficiary: beneficiary };
          await dispatch(cancelCertificates(apiBody)).unwrap();
          break;
        default:
          apiBody = { ...apiBody, target_id: selectedAccount };
          await dispatch(transferCertificates(apiBody)).unwrap();
          break;
      }

      setVisible(false); // Close the dialog after confirming
      setAccountError(false);
      props.updateCertificateActionDialog(null);
      props.setSelectedRowKeys([]);
      message.success(
        `${
          props.dialogAction.charAt(0).toUpperCase() +
          props.dialogAction.slice(1)
        } successful 🎉`,
        2
      );

      props.fetchCertificatesData();
    } catch (error) {
      message.error(
        `${
          props.dialogAction.charAt(0).toUpperCase() +
          props.dialogAction.slice(1)
        } failed: ${error.message.split(",")[0]}`,
        3
      );
    }
  };

  const handleTransferTypeChange = (e) => {
    setTransferType(e.target.value);
  };

  return (
    <Modal
      title={
        props.dialogAction === "transfer"
          ? `Transferring - ${props.selectedRowKeys.length} certificates`
          : `Canceling - ${props.selectedRowKeys.length} certificates`
      }
      open={visible}
      onOk={handleOk}
      onCancel={handleCancel}
      okText={
        props.dialogAction === "transfer"
          ? "Transfer Certificates"
          : "Cancel Certificates"
      }
      cancelText="Cancel"
      okButtonProps={{
        style:
          props.dialogAction === "cancel"
            ? {
                backgroundColor: "#F04438",
              }
            : {
                backgroundColor: "#3F6CF7",
              },
      }}
    >
      <p>
        You have selected {props.totalProduction / 1e6} MWh of certificates to{" "}
        {props.dialogAction} from:{" "}
      </p>
      <ul>
        {props.selectedDevices.map((device, index) => (
          <li key={index}>{props.getDeviceName(device)}</li>
        ))}
      </ul>
      <div>
        <span>Choose Certificates by:</span>
        <Radio.Group
          onChange={handleTransferTypeChange}
          value={transferType}
          style={{ marginLeft: "12px" }}
        >
          <Radio value="percentage">Percentage</Radio>
          <Radio value="quantity">Quantity</Radio>
        </Radio.Group>
      </div>

      {transferType === "percentage" ? (
        <div style={{ marginTop: "24px" }}>
          <label>Certificate percentage</label>
          <Input
            type="number"
            value={percentage}
            onChange={(e) => setPercentage(e.target.value)}
            suffix="%"
            style={{ width: "100%" }}
          />
        </div>
      ) : (
        <div style={{ marginTop: "24px" }}>
          <label>Certificate quantity</label>
          <Input
            type="number"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            style={{ width: "100%" }}
          />
        </div>
      )}
      {conditionalRendering()}
    </Modal>
  );
});

export default TransferCertificatesDialog;
