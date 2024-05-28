import React from 'react';
import { Form, Select, Input, Button } from 'antd';

const DeviceUnregisterForm = ({ onUnregister, selectedDevice }) => {
  const [form] = Form.useForm();

  const onFinish = (values) => {
    onUnregister(selectedDevice.id);
    form.resetFields();
  };

  return (
    <Form form={form} onFinish={onFinish} layout='vertical'>
      <Form.Item
        name="deviceId"
        label="Device ID"
        rules={[{ required: true, message: 'Please input the device ID!' }]}
      >
        <Input placeholder="Device ID" />
      </Form.Item>
      <Form.Item>
        <Button type="primary" htmlType="submit">
          Unregister
        </Button>
      </Form.Item>
    </Form>
  );
};

export default DeviceUnregisterForm;