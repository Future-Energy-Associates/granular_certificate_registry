import React from 'react';
import { List } from 'antd';

const ProductionDeviceList = ({ devices }) => {
  return (
    <List
      bordered={true}
      dataSource={devices}
      renderItem={(device) => <List.Item>{device.name}</List.Item>}
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

export default ProductionDeviceList;