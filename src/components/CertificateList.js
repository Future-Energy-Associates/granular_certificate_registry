import React from 'react';
import { List } from 'antd';

const CertificateList = ({ certificates }) => {
  return (
    <List
      header={<div>Certificates:</div>}
      bordered
      dataSource={certificates}
      renderItem={(certificate) => <List.Item>{certificate.id}</List.Item>}
    />
  );
};

export default CertificateList;