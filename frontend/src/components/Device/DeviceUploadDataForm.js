import React, { useState, forwardRef, useImperativeHandle } from "react";
import { Modal, Button, Space, Typography, Upload, message } from "antd";
import {
  DownloadOutlined,
  UploadOutlined,
  CalendarOutlined,
  LoadingOutlined,
} from "@ant-design/icons";
import {
  submitMeterReadingsAPI,
  downloadMeterReadingsTemplateAPI,
} from "../../api/deviceAPI";

const { Text } = Typography;

const DeviceUploadDialog = forwardRef((props, ref) => {
  const [visible, setVisible] = useState(false);
  const [deviceInfo, setDeviceInfo] = useState(null);
  console.log(deviceInfo);
  const [fileList, setFileList] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [messageApi, contextHolder] = message.useMessage();

  useImperativeHandle(ref, () => ({
    openDialog: (info) => {
      setDeviceInfo(info);
      setVisible(true);
    },
    closeDialog: () => setVisible(false),
  }));

  const handleCancel = () => {
    setFileList([]);
    setVisible(false);
  };

  const handleDownloadTemplate = async () => {
    try {
      const response = await downloadMeterReadingsTemplateAPI();
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "meter_readings_template.csv");
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      messageApi.error("Failed to download template");
      console.error("Download template error:", error);
    }
  };

  const handleSubmit = async () => {
    if (!fileList.length) {
      messageApi.warning("Please select a file to upload");
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", fileList[0]);
      formData.append("deviceID", deviceInfo?.deviceID);
      formData.append("accountID", deviceInfo?.accountID);

      const response = await submitMeterReadingsAPI(formData);

      messageApi.success({
        content: "Meter readings submitted successfully!",
        duration: 5,
        onClose: () => {
          setVisible(false);
          setFileList([]);
        },
      });

      // Show submission summary
      Modal.success({
        title: "Submission Summary",
        content: (
          <div>
            <p>
              Total device usage: {response.data.total_device_usage / 1e6} MWh
            </p>
            <p>
              First reading:{" "}
              {new Date(response.data.first_reading_datetime).toLocaleString()}
            </p>
            <p>
              Last reading:{" "}
              {new Date(response.data.last_reading_datetime).toLocaleString()}
            </p>
          </div>
        ),
      });
    } catch (error) {
      messageApi.error("Failed to submit meter readings");
      console.error("Submit readings error:", error);
    } finally {
      setUploading(false);
    }
  };

  const uploadProps = {
    beforeUpload: (file) => {
      const isCsv = file.type === "text/csv" || file.name.endsWith(".csv");
      if (!isCsv) {
        messageApi.error("You can only upload CSV files!");
        return false;
      }
      setFileList([file]);
      return false; // Prevent automatic upload
    },
    fileList,
    onRemove: () => {
      setFileList([]);
    },
  };

  return (
    <>
      {contextHolder}
      <Modal
        title={
          <Space direction="vertical" size={2} style={{ width: "100%" }}>
            <div>
              <Text strong>Upload Data - {deviceInfo?.deviceName} </Text>
              <Text type="secondary">({deviceInfo?.deviceLocalID})</Text>
            </div>
            <Text type="secondary">Date of the latest certificate:</Text>
            <Space>
              <CalendarOutlined style={{ color: "#5F6368" }} />
              <Text type="secondary" strong>
                {new Date().toLocaleDateString()}
              </Text>
            </Space>
          </Space>
        }
        open={visible}
        onCancel={handleCancel}
        footer={[
          <Button key="cancel" onClick={handleCancel}>
            Cancel
          </Button>,
          <Button
            key="submit"
            type="primary"
            onClick={handleSubmit}
            loading={uploading}
            disabled={fileList.length === 0}
            style={{
              backgroundColor: fileList.length > 0 ? "#043DDC" : "#F5F5F5",
              color: fileList.length > 0 ? "#FFFFFF" : "#00000040",
            }}
          >
            Submit meter readings
          </Button>,
        ]}
        width={480}
      >
        <Space direction="vertical" size={16} style={{ width: "100%" }}>
          <Space direction="vertical" size={4}>
            <Text strong>Upload Metering Data</Text>
            <Text type="secondary">
              Metering data for this device can be uploaded, this will trigger
              issuance of certificates for the device. Please download the CSV
              template below for details of the format to upload the data in:
            </Text>
            <Button
              type="link"
              icon={<DownloadOutlined />}
              onClick={handleDownloadTemplate}
              style={{ color: "#043DDC", fontWeight: 600, paddingLeft: 0 }}
            >
              Download CSV template
            </Button>
          </Space>

          <Upload.Dragger {...uploadProps}>
            <p className="ant-upload-drag-icon">
              {uploading ? <LoadingOutlined /> : <UploadOutlined />}
            </p>
            <p className="ant-upload-text">
              Click or drag CSV file to this area to upload
            </p>
            <p className="ant-upload-hint">
              Support for single CSV file upload only
            </p>
          </Upload.Dragger>
        </Space>
      </Modal>
    </>
  );
});

export default DeviceUploadDialog;
