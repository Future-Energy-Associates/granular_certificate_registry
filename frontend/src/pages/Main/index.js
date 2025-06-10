import React, { useState, useMemo, useEffect, useRef } from "react";
import { Outlet } from "react-router-dom";

import { useDispatch, useSelector } from "react-redux";
import { useNavigate, useLocation } from "react-router-dom";
import Cookies from "js-cookie";

import { Layout, Typography } from "antd";

import SideMenu from "../../components/Common/SideMenu";

const { Header, Sider, Content } = Layout;
const { Title } = Typography;

const Main = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const dynamicTitle = () => {
    switch (location.pathname) {
      default:
        return "Certificates";
      case "/certificates":
        return "Certificates";
      case "/devices":
        return "Device  management ";
      case "/account-management":
        return "Setting";
      case "/transfer-history":
        return "Transfer history";
    }
  };

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider
        width={224}
        style={{ background: "#fff", padding: "0 20px 0 10px" }}
      >
        <SideMenu />
      </Sider>

      <Layout>
        <Header
          style={{
            backgroundColor: "#fff",
            padding: "0 24px",
            borderBottom: "1px solid #E8EAED",
          }}
        >
          <Title level={3} style={{ margin: "16px 0", color: "#202124" }}>
            {dynamicTitle()}
          </Title>
        </Header>
        <Outlet /> {/* This renders nested routes (Dashboard, Profile, etc.) */}
      </Layout>
    </Layout>
  );
};

export default Main;
