import React from 'react';
import { Form, Select, Input, Button } from 'antd';

const ReserveForm = ({ onReserve, selectedAccount }) => {
  const [form] = Form.useForm();

  const onFinish = (values) => {
    onReserve(selectedAccount.id, values.certificateId);
    form.resetFields();
  };

  return (
    <Form form={form} onFinish={onFinish} layout='vertical'>
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
          Reserve
        </Button>
      </Form.Item>
    </Form>
  );
};

export default ReserveForm;