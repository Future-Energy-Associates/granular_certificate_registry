import React, { useState, forwardRef, useImperativeHandle } from "react";
import { Modal, Button, Space, Typography, Upload, message, Form, Input, Select, InputNumber } from "antd";
import {
  DownloadOutlined,
  UploadOutlined,
  CalendarOutlined,
  LoadingOutlined,
} from "@ant-design/icons";
import {
  downloadCertificateImportTemplateAPI,
  importCertificatesAPI,
} from "../../api/certificateAPI";
import { useAccount } from "../../context/AccountContext";
import { DEVICE_TECHNOLOGY_TYPE, ENERGY_SOURCE } from "../../enum";

const { Text } = Typography;
const { Option } = Select;

const CertificateImportDialog = forwardRef((props, ref) => {
  const { currentAccount } = useAccount();
  const [visible, setVisible] = useState(false);
  const [fileList, setFileList] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [messageApi, contextHolder] = message.useMessage();
  const [form] = Form.useForm();

  useImperativeHandle(ref, () => ({
    openDialog: () => {
      setVisible(true);
      // Reset form when opening
      form.resetFields();
    },
    closeDialog: () => setVisible(false),
  }));

  const handleCancel = () => {
    setFileList([]);
    form.resetFields();
    setVisible(false);
  };

  const handleDownloadTemplate = async () => {
    try {
      const response = await downloadCertificateImportTemplateAPI();
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "gc_import_template.csv");
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

    try {
      const formValues = await form.validateFields();
      setUploading(true);

      const formData = new FormData();
      formData.append("file", fileList[0]);
      formData.append("account_id", currentAccount?.detail?.id);
      
      // Create device JSON from form values
      const deviceData = {
        device_name: formValues.device_name,
        local_device_identifier: formValues.local_device_identifier,
        grid: formValues.grid,
        energy_source: formValues.energy_source,
        technology_type: formValues.technology_type,
        operational_date: formValues.operational_date,
        power_mw: parseFloat(formValues.power_mw),
        energy_mwh: parseFloat(formValues.energy_mwh),
        location: formValues.location,
        is_storage: formValues.is_storage || false,
        peak_demand: parseFloat(formValues.peak_demand),
      };
      
      formData.append("device_json", JSON.stringify(deviceData));

      const response = await importCertificatesAPI(formData);

      messageApi.success({
        content: "Certificates imported successfully!",
        duration: 5,
        onClose: () => {
          setVisible(false);
          setFileList([]);
          form.resetFields();
          // Refresh certificates data if callback provided
          if (props.onImportSuccess) {
            props.onImportSuccess();
          }
        },
      });

      // Show import summary
      Modal.success({
        title: "Import Summary",
        content: (
          <div>
            <p>
              Imported certificates: {response.data.number_of_imported_certificate_bundles}
            </p>
            <p>
              Total energy: {(response.data.total_imported_energy / 1e6).toFixed(3)} MWh
            </p>
          </div>
        ),
      });
    } catch (error) {
      messageApi.error(
        error?.response?.data?.detail || "Failed to import certificates"
      );
      console.error("Import error:", error);
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
              <Text strong>Import Granular Certificates</Text>
            </div>
            <Text type="secondary">Import certificate bundles from CSV file</Text>
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
            Import Certificates
          </Button>,
        ]}
        width={600}
      >
        <Space direction="vertical" size={16} style={{ width: "100%" }}>
          <Space direction="vertical" size={4}>
            <Text strong>Import Certificate Data</Text>
            <Text type="secondary">
              Certificate data can be imported via CSV file. Please download the CSV
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

          {fileList.length > 0 && (
            <Form form={form} layout="vertical">
              <Text strong>Device Information</Text>
              <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
                Provide device details for the imported certificates:
              </Text>
              
              <Form.Item
                name="device_name"
                label="Device Name"
                rules={[{ required: true, message: "Please enter device name" }]}
              >
                <Input placeholder="e.g., Solar Farm 1" />
              </Form.Item>

              <Form.Item
                name="local_device_identifier"
                label="Local Device Identifier"
                rules={[{ required: true, message: "Please enter device identifier" }]}
              >
                <Input placeholder="e.g., SF001" />
              </Form.Item>

              <Form.Item
                name="grid"
                label="Grid"
                rules={[{ required: true, message: "Please enter grid" }]}
              >
                <Input placeholder="e.g., ERCOT" />
              </Form.Item>

              <Form.Item
                name="energy_source"
                label="Energy Source"
                rules={[{ required: true, message: "Please select energy source" }]}
              >
                <Select placeholder="Select energy source">
                  {Object.entries(ENERGY_SOURCE).map(([key, value]) => (
                    <Option key={key} value={key.toLowerCase()}>
                      {value}
                    </Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item
                name="technology_type"
                label="Technology Type"
                rules={[{ required: true, message: "Please select technology type" }]}
              >
                <Select placeholder="Select technology type">
                  {Object.entries(DEVICE_TECHNOLOGY_TYPE).map(([key, value]) => (
                    <Option key={key} value={key.toLowerCase()}>
                      {value}
                    </Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item
                name="operational_date"
                label="Operational Date"
                rules={[{ required: true, message: "Please enter operational date" }]}
              >
                <Input placeholder="YYYY-MM-DD" />
              </Form.Item>

              <Form.Item
                name="power_mw"
                label="Device Power (MW)"
                initialValue={0}
                rules={[
                  {
                    required: true,
                    message: "Please enter maximum device power, if applicable"
                  },
                  {
                    type: "number",
                    min: 0,
                    message: "Device power cannot be negative"
                  }
                ]}
              >
                <InputNumber style={{ width: '100%' }} placeholder="e.g., 50.0" min={0} />
              </Form.Item>

              <Form.Item
                name="energy_mwh"
                label="Device Energy (MWh)"
                initialValue={0}
                rules={[
                  {
                    required: false,
                    message: "Please enter device energy storage capacity, if applicable"
                  },
                  {
                    type: "number",
                    min: 0,
                    message: "Device energy storage capacity cannot be negative"
                  }
                ]}
              >
                <InputNumber style={{ width: '100%' }} placeholder="e.g., 50.0" min={0} />
              </Form.Item>

              <Form.Item
                name="location"
                label="Location"
                rules={[{ required: true, message: "Please enter location" }]}
              >
                <Input placeholder="e.g., Texas, USA" />
              </Form.Item>

              <Form.Item
                name="peak_demand"
                label="Peak Demand (MW)"
                initialValue={0}
                rules={[
                  {
                    required: false,
                    message: "Please enter peak demand, if applicable"
                  },
                  {
                    type: "number",
                    min: 0,
                    message: "Peak demand cannot be negative"
                  }
                ]}
              >
                <InputNumber style={{ width: '100%' }} placeholder="e.g., 50.0" min={0} />
              </Form.Item>
            </Form>
          )}
        </Space>
      </Modal>
    </>
  );
});

export default CertificateImportDialog;