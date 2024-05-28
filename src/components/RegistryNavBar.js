import React from 'react';
import { Menu } from 'antd';

const RegistryNavBar = ({ registries, onRegistryClick, selectedRegistry }) => {
  return (
    <Menu mode="horizontal" selectedKeys={[selectedRegistry]}>
      {registries.map((registry) => (
        <Menu.Item key={registry.id} onClick={() => onRegistryClick(registry)}>
          {registry.name}
        </Menu.Item>
      ))}
    </Menu>
  );
};

export default RegistryNavBar;