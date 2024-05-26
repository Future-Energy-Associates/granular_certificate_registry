import React from 'react';
import { Card } from 'antd';

const Account = ({ account, certificates }) => {
  return (
    <Card title={`Account: ${account.name}`}>
      <p>Balance: {certificates.length}</p>
    </Card>
  );
};

export default Account;