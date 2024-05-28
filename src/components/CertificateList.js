import React from 'react';
import { List, Table } from 'antd';

const CertificateList = ({ certificates }) => {

  const columns = [
    {
      title: 'Issuance ID',
      dataIndex: 'issuance_id',
      key: 'issuance_id',
      rowScope: 'row',
    },
    {
      title: 'Device ID',
      dataIndex: 'device_id',
      key: 'device_id',
    },
    {
      title: 'Bundle Start ID',
      dataIndex: 'bundle_start_id',
      key: 'bundle_start_id',
    },
    {
      title: 'Bundle End ID',
      dataIndex: 'bundle_end_id',
      key: 'bundle_end_id',
    },
    {
      title: 'Quantity',
      dataIndex: 'quantity',
      key: 'quantity',
    },
    {
      title: 'Generation Time',
      dataIndex: 'generation_time',
      key: 'generation_time',
    },
  ];

  return (
    <div>
      <Table
        dataSource={certificates}
        columns={columns}
        rowKey="issuance_id"
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


  // return (
  //   <List
  //     bordered={true}
  //     headerBgColor="white"
  //     dataSource={certificates}
  //     renderItem={(certificate) => <List.Item>{certificate.id}</List.Item>}
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
};

export default CertificateList;