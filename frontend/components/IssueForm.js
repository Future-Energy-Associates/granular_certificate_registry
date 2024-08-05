import React from 'react';
import { Form, Select, Input, Button } from 'antd';

const IssueForm = ({ onIssue, devices, selectedDevice, selectedAccount }) => {
  const [form] = Form.useForm();

  const onFinish = (values) => {
    onIssue(selectedDevice.id, values.certificateId);
    form.resetFields();
  };

  return (
    <Form form={form} onFinish={onFinish} layout='vertical'>
      <Form.Item label="Account">
        <Input value={selectedAccount.name} disabled />
      </Form.Item>
      <Form.Item
        name="device"
        label="To Device"
        rules={[{ required: true, message: 'Please select the device to issue to!' }]}
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
      <Form.Item
        name="certificateId"
        label="Certificate ID"
        rules={[{ required: true, message: 'Please input the certificate ID!' }]}
      >
        <Input placeholder="Certificate ID" />
      </Form.Item>
      <Form.Item>
        <Button type="primary" htmlType="submit">
          Issue
        </Button>
      </Form.Item>
    </Form>
  );
};

export default IssueForm;