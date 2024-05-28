import React from 'react';
import { List } from 'antd';

const CertificateList = ({ certificates }) => {
  return (
    <List
      bordered={true}
      headerBgColor="white"
      dataSource={certificates}
      renderItem={(certificate) => <List.Item>{certificate.id}</List.Item>}
      style={{ backgroundColor: 'white' }}
      size="large"
      pagination={{
        onChange: (page) => {
          console.log(page);
        },
        pageSize: 10,
      }}
    />
  );
};

export default CertificateList;