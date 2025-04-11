import React, { useEffect } from "react";
import {
  Layout,
  Form,
  Row,
  Col,
  Input,
  Select,
  Avatar,
  Upload,
  Typography,
  Divider,
} from "antd";
import { UploadOutlined, UserOutlined } from "@ant-design/icons";
import sampleAvatar from "../../../assets/images/sample-avatar.jpeg";
import { useUser } from "../../../context/UserContext";

const { Content } = Layout;
const { Text } = Typography;
const { Option } = Select;

const AccountManagement = () => {
  const { userData } = useUser();
  const [form] = Form.useForm();

  // Helper to format user role (example)
  const formatUserRole = (userRole) => {
    switch (userRole) {
      case "TRADING":
        return "Trading User";
      case "AUDIT":
        return "Audit User";
      default:
        return "Admin";
    }
  };

  useEffect(() => {
    if (userData) {
      const { username = "", email = "", role = "" } = userData.userInfo;
      const nameParts = username.split(" ");
      const firstName = nameParts[0] || "";
      const lastName = nameParts[1] || "";

      form.setFieldsValue({
        firstName,
        lastName,
        email,
        role: formatUserRole(role),
      });
    }
  }, [userData, form]);

  return (
    <Layout>
      <Content
        style={{
          width: "100%",
          padding: "24px",
        }}
      >
        {/* FIRST NAME AND LAST NAME */}
        <Form
          form={form}
          layout="horizontal"
          labelCol={{
            span: 8,
            style: {
              paddingRight: "16px",
              display: "flex",
              justifyContent: "flexStart",
              color: "#3C4043",
            },
          }}
          wrapperCol={{ span: 8 }}
          colon={false} // This removes the colon after the label
        >
          <Form.Item label={<Text strong>Name</Text>} required>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="firstName"
                  noStyle
                  rules={[
                    { required: true, message: "Please enter your first name" },
                  ]}
                >
                  <Input placeholder="Olivia" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="lastName"
                  noStyle
                  rules={[
                    { required: true, message: "Please enter your last name" },
                  ]}
                >
                  <Input placeholder="Olivia" />
                </Form.Item>
              </Col>
            </Row>
          </Form.Item>
          <Divider />

          {/* EMAIL ADDRESS */}
          <Form.Item
            label={<Text strong>Email address</Text>}
            name="email"
            rules={[{ required: true, message: "Please enter your email" }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="olivia@untitledui.com"
            />
          </Form.Item>
          <Divider />
          {/* PHOTO UPLOAD */}
          <Form.Item
            label={<Text strong>Your photo</Text>}
            extra="This will be displayed on your profile."
          >
            <Row gutter={16} align="middle">
              {/* Avatar Preview */}
              <Col>
                <Avatar
                  size={64}
                  src={sampleAvatar}
                  style={{
                    border: "2px solid #d9d9d9",
                  }}
                />
              </Col>

              {/* Upload Area (Drag and Drop) */}
              <Col flex="auto">
                <Upload.Dragger
                  name="avatar"
                  multiple={false}
                  showUploadList={false}
                  style={{
                    borderRadius: 8,
                    border: "1px dashed #d9d9d9",
                    background: "#fafafa",
                    padding: 20,
                  }}
                >
                  <p className="ant-upload-drag-icon">
                    <UploadOutlined style={{ fontSize: 24 }} />
                  </p>
                  <p className="ant-upload-text">
                    Click to upload or drag and drop
                  </p>
                  <p className="ant-upload-hint">
                    SVG, PNG, JPG, or GIF (max. 800×400px)
                  </p>
                </Upload.Dragger>
              </Col>
            </Row>
          </Form.Item>
          <Divider />
          {/* ROLE SELECTION */}
          <Form.Item
            label={<Text strong>Role</Text>}
            name="role"
            rules={[{ required: true, message: "Please select a role" }]}
          >
            <Select placeholder="Select a role">
              <Option value="Admin">Admin</Option>
              <Option value="Production User">Production User</Option>
              <Option value="Trading User">Trading User</Option>
              <Option value="Audit User">Audit User</Option>
            </Select>
          </Form.Item>
        </Form>
      </Content>
    </Layout>
  );
};

export default AccountManagement;
