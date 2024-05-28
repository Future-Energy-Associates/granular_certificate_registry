import React from 'react';
import { Form, Select, Input, Button } from 'antd';

const DeviceUnregisterForm = ({ onUnregister, devices }) => {
  const [form] = Form.useForm();

  const onFinish = (values) => {
    onUnregister(devices.id);
    form.resetFields();
  };

  return (
    <Form form={form} onFinish={onFinish} layout='vertical'>
      <Form.Item
        name="deviceId"
        label="Device ID"
        rules={[{ required: true, message: 'Please input the device ID!' }]}
      >
        <Select placeholder="Select device">
          {devices
            .map((device) => (
              <Select.Option key={device.id} value={device.id}>
                {device.name}
              </Select.Option>
            ))}
        </Select>
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