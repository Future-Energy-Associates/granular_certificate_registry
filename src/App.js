import React, { useState, useEffect } from 'react';
import { Layout, Menu, Typography } from 'antd';
import Account from './components/Account';
import CertificateList from './components/CertificateList';
import TransferForm from './components/TransferForm';
import ActionBar from './components/ActionBar';
import CancelForm from './components/CancelForm';

const { Header, Content, Sider } = Layout;
const { Title } = Typography;

const App = () => {
  const [accounts, setAccounts] = useState([
    { id: 1, name: 'Account 1', certificates: [] },
    { id: 2, name: 'Account 2', certificates: [] },
  ]);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [selectedAction, setSelectedAction] = useState('transfer');

  useEffect(() => {
    if (accounts.length > 0) {
      setSelectedAccount(accounts[0]);
    }
  }, [accounts]);

  const handleAccountClick = (account) => {
    setSelectedAccount(account);
  };

  const handleActionClick = (action) => {
    setSelectedAction(action);
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

  const renderActionComponent = () => {
    switch (selectedAction) {
      case 'transfer':
        return (
          <TransferForm
            onTransfer={handleTransfer}
            accounts={accounts}
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
        return <div>Reserve Form</div>;
      case 'issue':
        return <div>Issue Form</div>;
      default:
        return null;
    }
  };

  return (
    <Layout>
      <Header>
        <Title level={2} style={{ color: 'white' }}>
          FEA Granular Certificate Registry
        </Title>
      </Header>
      <Layout>
        <Sider width={200}>
          <Menu mode="inline" style={{ height: '100%' }} selectedKeys={[selectedAccount?.id.toString()]}>
            {accounts.map((account) => (
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
              <CertificateList certificates={selectedAccount.certificates} />
              <ActionBar onActionClick={handleActionClick} />
              {renderActionComponent()}
            </div>
          )}
        </Content>
      </Layout>
    </Layout>
  );
};

export default App;