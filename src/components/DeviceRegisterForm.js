import React from 'react';
import { Form, Select, Input, Button } from 'antd';

const DeviceRegisterForm = ({ onRegister, selectedAccount }) => {
  const [form] = Form.useForm();

  const onFinish = (values) => {
    onRegister(selectedAccount.id);
    form.resetFields();
  };

  return (
    <Form form={form} onFinish={onFinish} layout='vertical'>
      <Form.Item label="Account">
        <Input value={selectedAccount.name} disabled />
      </Form.Item>
      <Form.Item
        name="deviceName"
        label="Device Name"
        rules={[{ required: true, message: 'Please input the name of the device.' }]}
      >
        <Input placeholder="Device Name" />
      </Form.Item>
      <Form.Item
        name="capacity"
        label="Capacity (MW)"
        rules={[{ required: true, message: 'Please input the capacity of the device.' }]}
      >
        <Input placeholder="Capacity" />
      </Form.Item>
      <Form.Item>
        <Button type="primary" htmlType="submit">
          Register
        </Button>
      </Form.Item>
    </Form>
  );
};

export default DeviceRegisterForm;