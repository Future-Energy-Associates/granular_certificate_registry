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
        name="issuance_id"
        label="GC Issuance ID"
        rules={[{ required: true, message: 'Please input the certificate issuance ID.' }]}
      >
        <Input placeholder="GC Issuance ID" />
      </Form.Item>
      <Form.Item
        name="bundle_start_id"
        label="From Bundle ID"
        rules={[{ required: true, message: 'Please input the first Bundle ID to select from.' }]}
      >
        <Input placeholder="Bunde Start ID" />
      </Form.Item>
      <Form.Item
        name="bundle_end_id"
        label="To Bundle ID"
        rules={[{ required: true, message: 'Please input the last Bundle ID to select to.' }]}
      >
        <Input placeholder="Bundle End ID" />
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