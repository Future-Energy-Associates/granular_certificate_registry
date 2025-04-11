import React, { useState, forwardRef, useImperativeHandle } from "react";
import { Modal, Input, Select, DatePicker, Checkbox, Form } from "antd";

import { useDispatch, useSelector } from "react-redux";
import { useAccount } from "../../context/AccountContext.js";

import { createDevice } from "../../store/device/deviceThunk";
import { getAccountDetails } from "../../store/account/accountThunk";

import { ENERGY_SOURCE, DEVICE_TECHNOLOGY_TYPE } from "../../enum";

const { Option } = Select;

const DeviceRegisterDialog = forwardRef((props, ref) => {
  const dispatch = useDispatch();
  const [visible, setVisible] = useState(false);
  const [form] = Form.useForm();

  const { currentAccount, saveAccountDetail } = useAccount();

  useImperativeHandle(ref, () => ({
    openDialog: () => setVisible(true),
    closeDialog: () => setVisible(false),
  }));

  const handleCancel = () => {
    form.resetFields();
    setVisible(false);
  };

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      values.location = `${values.location.latitude}, ${values.location.longitude}`;
      console.log("Device registration values:", values);
      const response = await dispatch(
        createDevice({ ...values, account_id: currentAccount.detail.id })
      ).unwrap();
      console.log("Create Device Response: ", response);
      const account = await dispatch(
        getAccountDetails(currentAccount.detail.id)
      ).unwrap();
      saveAccountDetail(account);
      setVisible(false);
    } catch (error) {
      console.error("Validation failed:", error);
    }
  };

  return (
    <Modal
      title="Add Device"
      open={visible}
      onOk={handleOk}
      onCancel={handleCancel}
      okText="Add Device"
      cancelText="Cancel"
      width={600}
    >
      <Form form={form} layout="vertical" initialValues={{ is_storage: false }}>
        <Form.Item
          label="Device Name"
          name="device_name"
          rules={[{ required: true, message: "Please input device name" }]}
        >
          <Input />
        </Form.Item>

        <Form.Item
          label="Device ID"
          name="local_device_identifier"
          rules={[{ required: true, message: "Please input device ID" }]}
          help="A unique identifier for the device, ideally used by the grid operator to identify the device and link it to available data sources. This could be a meter number, a serial number, or other appropriate identifier"
        >
          <Input />
        </Form.Item>

        <Form.Item
          label="Grid"
          name="grid"
          rules={[{ required: true, message: "Please select grid" }]}
        >
          <Input />
        </Form.Item>

        <Form.Item
          label="Technology type"
          name="technology_type"
          rules={[{ required: true, message: "Please select technology type" }]}
        >
          <Select placeholder="Select...">
            {Object.entries(DEVICE_TECHNOLOGY_TYPE).map(([key, value]) => (
              <Option key={key} value={key.toLocaleLowerCase()}>
                {value}
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          label="Energy source"
          name="energy_source"
          rules={[{ required: true, message: "Please select energy source" }]}
        >
          <Select placeholder="Select...">
            {Object.entries(ENERGY_SOURCE).map(([key, value]) => (
              <Option key={key} value={key.toLocaleLowerCase()}>
                {value}
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          label="Operational date"
          name="operational_date"
          rules={[
            { required: true, message: "Please select operational date" },
          ]}
        >
          <DatePicker style={{ width: "100%" }} />
        </Form.Item>

        <Form.Item
          label="Device Capacity"
          name="capacity"
          rules={[{ required: true, message: "Please input device capacity" }]}
        >
          <Input suffix="MW" placeholder="Ex: 80" />
        </Form.Item>

        <Form.Item
          label="Peak Demand"
          name="peak_demand"
          rules={[{ required: true, message: "Please input peak demand" }]}
        >
          <Input suffix="MW" placeholder="Ex: 80" />
        </Form.Item>

        <Form.Item label="Location" rules={[{ required: true }]}>
          <Input.Group compact>
            <Form.Item
              name={["location", "latitude"]}
              noStyle
              rules={[{ required: true, message: "Latitude is required" }]}
            >
              <Input style={{ width: "50%" }} placeholder="Latitude" />
            </Form.Item>
            <Form.Item
              name={["location", "longitude"]}
              noStyle
              rules={[{ required: true, message: "Longitude is required" }]}
            >
              <Input style={{ width: "50%" }} placeholder="Longitude" />
            </Form.Item>
          </Input.Group>
        </Form.Item>

        <Form.Item
          name="is_storage"
          valuePropName="checked"
          rules={[{ required: true }]}
        >
          <Checkbox>Is storage device?</Checkbox>
        </Form.Item>
      </Form>
    </Modal>
  );
});

export default DeviceRegisterDialog;
