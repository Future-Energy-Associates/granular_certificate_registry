import React from 'react';
import { Menu } from 'antd';

const ProductionDeviceActionBar = ({ onActionClick }) => {
  const handleClick = (action) => {
    onActionClick(action);
  };

  return (
    <Menu mode="horizontal">
      <Menu.Item key="issue" onClick={() => handleClick('issue')}>
        Issue to Device
      </Menu.Item>
      <Menu.Item key="register" onClick={() => handleClick('register')}>
        Register New Device
      </Menu.Item>
      <Menu.Item key="unregister" onClick={() => handleClick('unregister')}>
        Unregister Device
      </Menu.Item>
      {/* Add more action items as needed */}
    </Menu>
  );
};

export default ProductionDeviceActionBar;