import React, { useState, useEffect } from 'react';
import { Layout, Menu, Typography } from 'antd';
import Account from './components/Account';
import CertificateList from './components/CertificateList';
import TransferForm from './components/TransferForm';
import CancelForm from './components/CancelForm';
import ReserveForm from './components/ReserveForm';
import IssueForm from './components/IssueForm';
import CertificateActionBar from './components/CertificateActionBar';
import RegistryNavBar from './components/RegistryNavBar';
import DeviceList from './components/DeviceList';
import DeviceActionBar from './components/DeviceActionBar'
import DeviceRegisterForm from './components/DeviceRegisterForm';
import DeviceUnregisterForm from './components/DeviceUnregisterForm';

import example_registries from './example_data';

const { Header, Content, Sider } = Layout;
const { Title } = Typography;

const App = () => {
  const [registries, setRegistries] = useState(example_registries);

  const [selectedRegistry, setSelectedRegistry] = useState(registries[0]?.id.toString());
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [selectedDeviceAction, setSelectedDeviceAction] = useState('issue');
  const [selectedCertificateAction, setSelectedCertificateAction] = useState('transfer');
  const [selectedView, setSelectedView] = useState('certificates');

  useEffect(() => {
    const registry = registries.find((r) => r.id.toString() === selectedRegistry);
    if (registry && registry.accounts.length > 0) {
      setSelectedAccount(registry.accounts[0]);
    }
  }, [registries, selectedRegistry]);

  useEffect(() => {
    if (selectedAccount && selectedAccount.devices.length > 0) {
      setSelectedDevice(selectedAccount.devices[0]);
    }
  }, [selectedAccount]);

  const handleRegistryClick = (registry) => {
    setSelectedRegistry(registry.id.toString());
  };

  const handleAccountClick = (account) => {
    setSelectedAccount(account);
  };

  const handleDeviceClick = (device) => {
    setSelectedDevice(device);
  };

  const handleCertificateActionClick = (action) => {
    setSelectedCertificateAction(action);
  };

  const handleTransfer = (fromAccount, toAccount, certificateId) => {
    // Perform the transfer logic here
    console.log(`Transferring certificate ${certificateId} from ${fromAccount} to ${toAccount}`);
  };

  const handleCancel = (certificateId) => {
    // Perform the cancel logic here
    console.log(`Cancelling certificate ${certificateId}`);
  };

  const handleReserve = (certificateId) => {
    // Perform the reserve logic here
    console.log(`Reserving certificate ${certificateId}`);
  };

  const handleIssue = (certificateId) => {
    // Perform the issue logic here
    console.log(`Issuing certificate ${certificateId}`);
  };

  const handleDeviceRegister = (device) => {
    // Perform the device register logic here
    console.log(`Registering device ${device}`);
  };

  const handleDeviceUnregister = (device) => {
    // Perform the device unregister logic here
    console.log(`Unregistering device ${device}`);
  };

  const handleViewClick = (view) => {
    setSelectedView(view);
  };

  const handleDeviceActionClick = (action) => {
    setSelectedDeviceAction(action);
  };

  const renderSelectedView = () => {
    switch (selectedView) {
      case 'certificates':
        return (
          <>
            <br />
            <CertificateList certificates={selectedAccount.certificates} />
            <br />
            <CertificateActionBar onActionClick={handleCertificateActionClick} />
            <br />
            {renderCertificateActionComponent()}
          </>
        );
      case 'devices':
        return (
          <>
            <br />
            <DeviceList devices={selectedAccount.devices} />
            <br />
            <DeviceActionBar onActionClick={handleDeviceActionClick} />
            <br />
            {renderDeviceActionComponent()}
          </>
        );
      default:
        return null;
    }
  };

  const renderCertificateActionComponent = () => {
    switch (selectedCertificateAction) {
      case 'transfer':
        return (
          <TransferForm
            onTransfer={handleTransfer}
            accounts={registries.find((r) => r.id.toString() === selectedRegistry)?.accounts}
            selectedAccount={selectedAccount}
          />
        );
      case 'cancel':
        return (
            <CancelForm
              onTransfer={handleCancel}
              selectedAccount={selectedAccount}
            />
          );
      case 'reserve':
        return (
            <ReserveForm
              onReserve={handleReserve}
              selectedAccount={selectedAccount}
            />
          );
      default:
        return null;
    }
  };

  const renderDeviceActionComponent = () => {
    switch (selectedDeviceAction) {
      case 'issue':
        return (
          <IssueForm
            onIssue={handleIssue}
            devices={selectedAccount.devices}
            selectedDevice={selectedDevice}
            selectedAccount={selectedAccount}
          />
        );
      case 'register':
        return (
            <DeviceRegisterForm
              onDeviceRegister={handleDeviceRegister}
              selectedAccount={selectedAccount}
            />
          );
      case 'unregister':
        return (
            <DeviceUnregisterForm
              onDeviceUnregister={handleDeviceUnregister}
              devices={selectedAccount.devices}
            />
          );
      default:
        return null;
    }
  };



  return (
    <Layout>
      <Header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Title level={2} style={{ color: 'white', margin: 0 }}>
          FEA Granular Certificate Registry
        </Title>
      </Header>
      <RegistryNavBar
        registries={registries}
        onRegistryClick={handleRegistryClick}
        selectedRegistry={selectedRegistry}
      />
      <Layout>
        <Sider width={200}>
          <Menu
            mode="inline"
            style={{ height: '100%' }}
            selectedKeys={[selectedAccount?.id.toString()]}
          >
            {registries
              .find((r) => r.id.toString() === selectedRegistry)
              ?.accounts.map((account) => (
                <Menu.Item key={account.id} onClick={() => handleAccountClick(account)}>
                  {account.name}
                </Menu.Item>
              ))}
          </Menu>
        </Sider>
        <Content style={{ padding: '24px' }}>
          {selectedAccount && (
            <div>
              <Account account={selectedAccount} certificates={selectedAccount.certificates} />
              <Menu mode="horizontal" selectedKeys={[selectedView]} onClick={({ key }) => handleViewClick(key)}>
                <Menu.Item key="certificates">Certificates</Menu.Item>
                <Menu.Item key="devices">Production Devices</Menu.Item>
              </Menu>
              {renderSelectedView()}
          </div>
          )}
        </Content>
      </Layout>
    </Layout>
  );
};

export default App;