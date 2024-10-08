import React from 'react';
import { Form, Select, Input, Button } from 'antd';

const TransferForm = ({ onTransfer, accounts, selectedAccount }) => {
  const [form] = Form.useForm();

  const onFinish = (values) => {
    onTransfer(selectedAccount.id, values.toAccount, values.certificateId);
    form.resetFields();
  };

  return (
    <Form form={form} onFinish={onFinish} layout='vertical'>
      <Form.Item label="From Account">
        <Input value={selectedAccount.name} disabled />
      </Form.Item>
      <Form.Item
        name="toAccount"
        label="To Account"
        rules={[{ required: true, message: 'Please select the to account!' }]}
      >
        <Select placeholder="Select the to account">
          {accounts
            .filter((account) => account.id !== selectedAccount.id)
            .map((account) => (
              <Select.Option key={account.id} value={account.id}>
                {account.name}
              </Select.Option>
            ))}
        </Select>
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
          Transfer
        </Button>
      </Form.Item>
    </Form>
  );
};

export default TransferForm;