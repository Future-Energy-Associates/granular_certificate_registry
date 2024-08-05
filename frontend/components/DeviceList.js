import React from 'react';
import { Table, List, Typography } from 'antd';

const { Text } = Typography;

const ProductionDeviceList = ({ devices }) => {

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      rowScope: 'row',
    },
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Capacity',
      dataIndex: 'capacity',
      key: 'capacity',
    },
  ];

  return (
    <div>
      <Table
        dataSource={devices}
        columns={columns}
        rowKey="id"
        tableLayout='auto'
        scroll={{ x: 'max-content' }}
        style={{ backgroundColor: 'white' }}
        size="large"
        pagination={{
          onChange: (page) => {
            console.log(page);
          },
          pageSize: 10,
          position: ['bottomLeft'],
        }}
      />
    </div>
  );
};

  // return (
  //   <List
  //     bordered={true}
  //     dataSource={devices}
  //     itemLayout='horizontal'
  //     renderItem={(device) => (
  //       <List.Item>
  //         <div>
  //           <div>
  //             <Text strong>{device.name}</Text>
  //             <Text type="secondary" style={{ marginLeft: '8px' }}>
  //               (ID: {device.id})
  //             </Text>
  //           </div>
  //           <div style={{ marginTop: '4px' }}>
  //             <Text>Capacity (MW): {device.capacity}</Text>
  //           </div>
  //         </div>
  //       </List.Item>
  //     )}
  //     style={{ backgroundColor: 'white' }}
  //     size="large"
  //     pagination={{
  //       onChange: (page) => {
  //         console.log(page);
  //       },
  //       pageSize: 10,
  //       align: 'start',
  //     }}
  //   />
  // );
// };

export default ProductionDeviceList;