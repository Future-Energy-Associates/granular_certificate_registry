import React from 'react';
import { Card } from 'antd';

const Account = ({ account, certificates
 }) => {
  return (
    <Card title={`Account: ${account.name}`}>
      <p>Total MWh: {certificates.length}</p>
      <p>Number of Devices: {account.devices.length}</p>
    </Card>
  );
};

export default Account;