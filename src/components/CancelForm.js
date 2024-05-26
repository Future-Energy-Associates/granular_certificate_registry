import React from 'react';
import { Form, Select, Input, Button } from 'antd';

const CancelForm = ({ onCancel, selectedAccount }) => {
  const [form] = Form.useForm();

  const onFinish = (values) => {
    onCancel(selectedAccount.id, values.certificateId);
    form.resetFields();
  };

  return (
    <Form form={form} onFinish={onFinish}>
      <Form.Item label="Account">
        <Input value={selectedAccount.name} disabled />
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
          Cancel
        </Button>
      </Form.Item>
    </Form>
  );
};

export default CancelForm;