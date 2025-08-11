import React, { useEffect, useState } from "react";
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
  Button,
  Table,
  Tag,
  Space,
  InputNumber,
  Modal,
  Popconfirm,
  message,
} from "antd";
import { UploadOutlined, UserOutlined } from "@ant-design/icons";
import sampleAvatar from "../../../assets/images/gcos_avatar.png";
import { useUser } from "../../../context/UserContext";
import { createApiKeyAPI, listApiKeysAPI, deactivateApiKeyAPI } from "../../../api/authAPI";

const { Content } = Layout;
const { Text } = Typography;
const { Option } = Select;

const AccountManagement = () => {
  const { userData } = useUser();
  const [form] = Form.useForm();
  const [apiForm] = Form.useForm();

  const [apiKeys, setApiKeys] = useState([]);
  const [loadingKeys, setLoadingKeys] = useState(false);
  const [creatingKey, setCreatingKey] = useState(false);
  const [showKeyModal, setShowKeyModal] = useState(false);
  const [createdKeyInfo, setCreatedKeyInfo] = useState(null); // { id, name, key, expires, created_at }

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

  const fetchApiKeys = async () => {
    try {
      setLoadingKeys(true);
      const resp = await listApiKeysAPI();
      setApiKeys(resp?.data || []);
    } catch (err) {
      message.error("Failed to load API keys");
    } finally {
      setLoadingKeys(false);
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

  useEffect(() => {
    fetchApiKeys();
  }, []);

  const onCreateApiKey = async (values) => {
    try {
      setCreatingKey(true);
      const payload = {
        name: values.apiKeyName,
        expires_days: values.expiresDays ?? null,
      };
      const resp = await createApiKeyAPI(payload);
      const data = resp?.data;
      setCreatedKeyInfo(data);
      setShowKeyModal(true);
      apiForm.resetFields();
      await fetchApiKeys();
      message.success("API key created");
    } catch (err) {
      const msg = err?.message || "Failed to create API key";
      message.error(msg);
    } finally {
      setCreatingKey(false);
    }
  };

  const onDeactivate = async (id) => {
    try {
      await deactivateApiKeyAPI(id);
      message.success("API key deactivated");
      await fetchApiKeys();
    } catch (err) {
      message.error("Failed to deactivate API key");
    }
  };

  const columns = [
    { title: "Name", dataIndex: "name", key: "name" },
    {
      title: "Created",
      dataIndex: "created_at",
      key: "created_at",
      render: (v) => (v ? new Date(v).toLocaleString() : "-"),
    },
    {
      title: "Expires",
      dataIndex: "expires",
      key: "expires",
      render: (v) => (v ? new Date(v).toLocaleString() : "-"),
    },
    {
      title: "Status",
      dataIndex: "is_active",
      key: "is_active",
      render: (active) =>
        active ? <Tag color="green">Active</Tag> : <Tag color="red">Inactive</Tag>,
    },
    {
      title: "Actions",
      key: "actions",
      render: (_, record) =>
        record.is_active ? (
          <Space>
            <Popconfirm
              title="Deactivate API key"
              description="This will deactivate the API key immediately. Continue?"
              okText="Deactivate"
              okType="danger"
              onConfirm={() => onDeactivate(record.id)}
            >
              <Button danger size="small">Deactivate</Button>
            </Popconfirm>
          </Space>
        ) : null,
    },
  ];

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
          colon={false}
        >
          <Form.Item label={<Text strong>Name</Text>} required>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="firstName"
                  noStyle
                  rules={[{ required: true, message: "Please enter your first name" }]}
                >
                  <Input placeholder="Olivia" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="lastName"
                  noStyle
                  rules={[{ required: true, message: "Please enter your last name" }]}
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
            <Input prefix={<UserOutlined />} placeholder="olivia@untitledui.com" />
          </Form.Item>
          <Divider />

          {/* PHOTO UPLOAD */}
          <Form.Item label={<Text strong>Your photo</Text>} extra="This will be displayed on your profile.">
            <Row gutter={16} align="middle">
              <Col>
                <Avatar
                  size={64}
                  src={sampleAvatar}
                  style={{
                    border: "2px solid #d9d9d9",
                  }}
                />
              </Col>

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
                  <p className="ant-upload-text">Click to upload or drag and drop</p>
                  <p className="ant-upload-hint">SVG, PNG, JPG, or GIF (max. 800×400px)</p>
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

        <Divider />

        {/* API KEY MANAGEMENT */}
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <Text strong style={{ fontSize: 16 }}>API Keys</Text>
          </Col>
          <Col span={24}>
            <Form form={apiForm} layout="inline" onFinish={onCreateApiKey}>
              <Form.Item
                name="apiKeyName"
                label="Name"
                rules={[{ required: true, message: "Please enter a name for the API key" }]}
              >
                <Input placeholder="My integration key" style={{ width: 280 }} />
              </Form.Item>
              <Form.Item name="expiresDays" label="Expires (days)">
                <InputNumber min={1} max={365} placeholder="default" />
              </Form.Item>
              <Form.Item>
                <Button type="primary" htmlType="submit" loading={creatingKey}>
                  Request API key
                </Button>
              </Form.Item>
            </Form>
          </Col>

          <Col span={24}>
            <Table
              rowKey="id"
              loading={loadingKeys}
              dataSource={apiKeys}
              columns={columns}
              pagination={{ pageSize: 5 }}
            />
          </Col>
        </Row>

        <Modal
          open={showKeyModal}
          onCancel={() => setShowKeyModal(false)}
          onOk={() => setShowKeyModal(false)}
          okText="I have copied it"
          title="Your API key (shown only once)"
        >
          {createdKeyInfo ? (
            <div>
              <p><strong>Name:</strong> {createdKeyInfo.name}</p>
              <p><strong>Key:</strong> <code>{createdKeyInfo.key}</code></p>
              <p><strong>Expires:</strong> {new Date(createdKeyInfo.expires).toLocaleString()}</p>
              <p style={{ marginTop: 8 }}>
                Please store this key securely. It will not be displayed again.
              </p>
            </div>
          ) : null}
        </Modal>
      </Content>
    </Layout>
  );
};

export default AccountManagement;
