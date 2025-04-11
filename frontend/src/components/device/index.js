import React, { useState, useMemo, useEffect, useRef } from "react";
import dayjs from "dayjs";

import { Layout, Button, Card, Col, Space, Input, Select } from "antd";

import {
  AppstoreOutlined,
  SwapOutlined,
  CloseCircleOutlined,
  LaptopOutlined,
  ThunderboltOutlined,
  PlusCircleOutlined,
  UploadOutlined,
  SearchOutlined,
} from "@ant-design/icons";

import "../../assets/styles/pagination.css";
import "../../assets/styles/filter.css";

import { useSelector } from "react-redux";
import { useAccount } from "../../context/AccountContext.js";
import { useNavigate } from "react-router-dom";

import DeviceRegisterDialog from "./DeviceRegisterForm";
import DeviceUploadDialog from "./DeviceUploadDataForm";
import Summary from "./Summary";

import FilterTable from "../common/FilterTable";

const { Option } = Select;
const { Search } = Input;

import { DEVICE_TECHNOLOGY_TYPE } from "../../enum";

const Device = () => {
  const navigate = useNavigate();

  const { userInfo } = useSelector((state) => state.user);
  const { currentAccount } = useAccount();
  const devices = currentAccount?.detail.devices || [];

  const interactAllowed =
    userInfo.role !== "TRADING_USER" && userInfo.role !== "AUDIT_USER";

  const defaultFilters = {
    device_id: null,
    technology_type: null,
  };

  const [filters, setFilters] = useState({});
  const [filteredDevices, setFiltersDevices] = useState(devices);
  const [searchKey, setSearchKey] = useState("");

  const deviceRegisterDialogRef = useRef();
  const deviceUploadDialogRef = useRef();

  const deviceOptions = useMemo(
    () =>
      devices.map((device) => ({
        value: device.id,
        label:
          `${device.device_name} (${device.local_device_identifier})` ||
          `Device (${device.local_device_identifier})`,
      })),
    [devices]
  );

  useEffect(() => {
    if (!interactAllowed) {
      navigate("/certificates");
      return;
    }

    // if (currentAccount && !currentAccount?.id) {
    //   navigate("/login");
    //   return;
    // }

    setFiltersDevices(devices);
  }, [currentAccount, devices, navigate]);

  const pageSize = 10;
  const totalPages = Math.ceil(devices?.length / pageSize);

  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const handleApplyFilter = () => {
    // Apply the filter logic here
    const filteredDevices = devices.filter((device) => {
      // Check each filter
      const matchedFilters =
        (filters.device_id ? device.id === filters.device_id : true) &&
        (filters.technology_type
          ? device.technology_type === filters.technology_type.toLowerCase()
          : true);

      const searchFilter = !!searchKey
        ? device.device_name.toLowerCase().includes(searchKey.toLowerCase()) ||
          device.local_device_identifier
            .toLowerCase()
            .includes(searchKey.toLowerCase())
        : true;

      return matchedFilters && searchFilter;
    });

    setFiltersDevices(filteredDevices);
  };

  const handleClearFilter = async () => {
    setFilters({});
    setSearchKey("");
    setFiltersDevices(devices);
  };

  const openDialog = () => {
    deviceRegisterDialogRef.current.openDialog(); // Open the dialog from the parent component
  };

  const closeDialog = () => {
    deviceRegisterDialogRef.current.closeDialog(); // Close the dialog from the parent component
  };

  const columns = [
    {
      title: <span style={{ color: "#80868B" }}>Device name & ID</span>,
      dataIndex: "device_name",
      key: "device_name",
      sorter: (a, b) => a.device_name.localeCompare(b.device_name),
    },
    {
      title: <span style={{ color: "#80868B" }}>Technology type</span>,
      dataIndex: "technology_type",
      key: "technology_type",
      render: (type) => {
        const upperKey = type?.toUpperCase().replace(/ /g, "_");
        return DEVICE_TECHNOLOGY_TYPE[upperKey] || type;
      },
      sorter: (a, b) => {
        // Sorting based on the raw value; adjust if needed
        return a.technology_type?.localeCompare(b.technology_type) || 0;
      },
    },
    {
      title: <span style={{ color: "#80868B" }}>Production start date</span>,
      dataIndex: "operational_date",
      key: "operational_date",
      render: (date) => (date ? dayjs(date).format("YYYY-MM-DD") : "-"),
      sorter: (a, b) => {
        // Convert dates to timestamps for comparison
        return new Date(a.operational_date) - new Date(b.operational_date);
      },
    },
    {
      title: <span style={{ color: "#80868B" }}>Device capacity (MW)</span>,
      dataIndex: "capacity",
      key: "capacity",
      render: (text) => <span style={{ color: "#5F6368" }}>{text}</span>,
      sorter: (a, b) => a.capacity - b.capacity,
    },
    {
      title: <span style={{ color: "#80868B" }}>Location</span>,
      dataIndex: "location",
      key: "location",
      render: (text) => <span style={{ color: "#5F6368" }}>{text}</span>,
    },
    {
      title: "",
      render: (_, row) => (
        <Button
          style={{ color: "#043DDC", fontWeight: "600" }}
          type="link"
          onClick={() =>
            deviceUploadDialogRef.current.openDialog({
              deviceName: row.device_name,
              deviceLocalID: row.local_device_identifier,
              deviceID: row.id,
            })
          }
        >
          <UploadOutlined /> Upload Data
        </Button>
      ),
    },
  ];

  const filterComponents = [
    <Search
      placeholder="Search for device..."
      onSearch={(value) => handleApplyFilter(value)}
      value={searchKey}
      onChange={(e) => setSearchKey(e.target.value)}
      enterButton={<SearchOutlined />}
      size="medium"
    />,
    /* Device Filter */
    <Select
      placeholder="Device"
      // mode="multiple"
      options={deviceOptions}
      value={filters.device_id}
      onChange={(value) => handleFilterChange("device_id", value)}
      style={{ width: 120 }}
      suffixIcon={<LaptopOutlined />}
      allowClear
    ></Select>,
    /* Technology Type filter */
    <Select
      placeholder="Technology Type"
      value={filters.technology_type}
      onChange={(value) => handleFilterChange("technology_type", value)}
      style={{ width: 150 }}
      suffixIcon={<ThunderboltOutlined />}
      allowClear
    >
      {Object.entries(DEVICE_TECHNOLOGY_TYPE).map(([key, value]) => (
        <Option key={key} value={key.toLocaleLowerCase()}>
          {value}
        </Option>
      ))}
    </Select>,
  ];

  const btnList = [
    {
      icon: <PlusCircleOutlined />,
      btnType: "primary",
      type: "add",
      style: { height: "40px" },
      name: "Add Device",
      handle: () => openDialog(),
    },
  ];

  return (
    <>
      <Layout>
        <FilterTable
          summary={<Summary />}
          tableName="Device management"
          columns={columns}
          filterComponents={filterComponents}
          tableActionBtns={btnList}
          defaultFilters={defaultFilters}
          filters={filters}
          dataSource={filteredDevices}
          handleClearFilter={handleClearFilter}
          handleApplyFilter={handleApplyFilter}
          isShowSelection={false}
        />
      </Layout>
      <DeviceRegisterDialog ref={deviceRegisterDialogRef} />
      <DeviceUploadDialog ref={deviceUploadDialogRef} />
    </>
  );
};

export default Device;
