import React from 'react';
import { Menu } from 'antd';

const ActionBar = ({ onActionClick }) => {
  const handleClick = (action) => {
    onActionClick(action);
  };

  return (
    <Menu mode="horizontal">
      <Menu.Item key="transfer" onClick={() => handleClick('transfer')}>
        Transfer
      </Menu.Item>
      <Menu.Item key="cancel" onClick={() => handleClick('cancel')}>
        Cancel
      </Menu.Item>
      <Menu.Item key="reserve" onClick={() => handleClick('reserve')}>
        Reserve
      </Menu.Item>
      <Menu.Item key="issue" onClick={() => handleClick('issue')}>
        Issue
      </Menu.Item>
    </Menu>
  );
};

export default ActionBar;