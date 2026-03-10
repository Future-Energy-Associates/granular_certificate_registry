import React, { useState, useMemo, useEffect } from "react";
import { Button, message, Select, DatePicker } from "antd";
import {
  DownloadOutlined,
  LaptopOutlined,
  ClockCircleOutlined,
  ThunderboltOutlined,
} from "@ant-design/icons";

import "../../assets/styles/pagination.css";
import "../../assets/styles/filter.css";

import { useDispatch, useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import { useAccount } from "../../context/AccountContext";
import {
  fetchStorageRecords,
  fetchAllocatedStorageRecords,
} from "../../store/storage/storageThunk";

import FilterTable from "../Common/FilterTable";
import { isEmpty } from "../../utils";

const { Option } = Select;
const { RangePicker } = DatePicker;

const Storage = () => {
  const { currentAccount } = useAccount();
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const { storageRecords, allocatedStorageRecords, loading } = useSelector(
    (state) => state.storage
  );

  const [storageSelectedRowKeys, setStorageSelectedRowKeys] = useState([]);
  const [storageSelectedRecords, setStorageSelectedRecords] = useState([]);
  const [allocatedSelectedRowKeys, setAllocatedSelectedRowKeys] = useState([]);
  const [allocatedSelectedRecords, setAllocatedSelectedRecords] = useState([]);

  // Get all devices for filtering - only storage devices
  const allDevices = useMemo(() => {
    return [
      ...(currentAccount?.detail?.devices || []).filter(device => device.is_storage === true),
    ];
  }, [currentAccount?.detail?.devices]);

  const deviceOptions = useMemo(() => {
    return allDevices.map((device) => ({
      value: device.id,
      label: device.device_name || `Device ${device.id}`,
    }));
  }, [allDevices]);

  // Storage Records Filters
  const defaultStorageFilters = {
    device_id: null,
    is_charging: null,
    flow_start_date: null,
    flow_end_date: null,
  };

  const [storageFilters, setStorageFilters] = useState(defaultStorageFilters);

  // Allocated Storage Records Filters
  const defaultAllocatedFilters = {
    device_id: null,
    efficiency_factor_start: null,
    efficiency_factor_end: null,
  };

  const [allocatedFilters, setAllocatedFilters] = useState(defaultAllocatedFilters);

  useEffect(() => {
    if (!currentAccount?.detail?.id) {
      navigate("/login");
      return;
    }
  }, [currentAccount, navigate]);

  useEffect(() => {
    if (allDevices.length > 0) {
      fetchStorageData();
    }
  }, [currentAccount, dispatch, allDevices]);

  const fetchStorageData = async () => {
    if (allDevices.length === 0) return;

    const deviceIds = allDevices.map(device => device.id);
    
    try {
      await Promise.all([
        dispatch(fetchStorageRecords(deviceIds)).unwrap(),
        dispatch(fetchAllocatedStorageRecords(deviceIds)).unwrap(),
      ]);
    } catch (error) {
      console.error("Failed to fetch storage data:", error);
      message.error(error?.message || "Failed to fetch storage data");
    }
  };

  const getDeviceName = (deviceId) => {
    const device = allDevices.find((device) => deviceId === device.id);
    return device?.device_name || `Device ${deviceId}`;
  };

  // Filter functions
  const filteredStorageRecords = useMemo(() => {
    return storageRecords.filter((record) => {
      const deviceMatch = !storageFilters.device_id || record.device_id === storageFilters.device_id;
      const chargingMatch = storageFilters.is_charging === null || record.is_charging === storageFilters.is_charging;
      
      let dateMatch = true;
      if (storageFilters.flow_start_date && storageFilters.flow_end_date) {
        const recordStart = new Date(record.flow_start_datetime);
        const filterStart = storageFilters.flow_start_date.toDate();
        const filterEnd = storageFilters.flow_end_date.toDate();
        dateMatch = recordStart >= filterStart && recordStart <= filterEnd;
      }

      return deviceMatch && chargingMatch && dateMatch;
    });
  }, [storageRecords, storageFilters]);

  const filteredAllocatedRecords = useMemo(() => {
    return allocatedStorageRecords.filter((record) => {
      const deviceMatch = !allocatedFilters.device_id || record.device_id === allocatedFilters.device_id;
      
      let dateMatch = true;
      if (allocatedFilters.efficiency_factor_start && allocatedFilters.efficiency_factor_end) {
        const recordStart = new Date(record.efficiency_factor_interval_start);
        const filterStart = allocatedFilters.efficiency_factor_start.toDate();
        const filterEnd = allocatedFilters.efficiency_factor_end.toDate();
        dateMatch = recordStart >= filterStart && recordStart <= filterEnd;
      }

      return deviceMatch && dateMatch;
    });
  }, [allocatedStorageRecords, allocatedFilters]);

  // Storage Records Filter Components
  const storageFilterComponents = [
    <Select
      placeholder="Device"
      options={deviceOptions}
      value={storageFilters.device_id}
      onChange={(value) => setStorageFilters(prev => ({ ...prev, device_id: value }))}
      style={{ width: 150 }}
      suffixIcon={<LaptopOutlined />}
      allowClear
    />,
    <Select
      placeholder="Flow Type"
      value={storageFilters.is_charging}
      onChange={(value) => setStorageFilters(prev => ({ ...prev, is_charging: value }))}
      style={{ width: 120 }}
      suffixIcon={<ThunderboltOutlined />}
      allowClear
    >
      <Option value={true}>Charging</Option>
      <Option value={false}>Discharging</Option>
    </Select>,
    <RangePicker
      value={[storageFilters.flow_start_date, storageFilters.flow_end_date]}
      onChange={(dates) => setStorageFilters(prev => ({ 
        ...prev, 
        flow_start_date: dates ? dates[0] : null,
        flow_end_date: dates ? dates[1] : null
      }))}
      allowClear={true}
      format="YYYY-MM-DD"
      placeholder={["Flow Start Date", "Flow End Date"]}
    />,
  ];

  // Allocated Storage Records Filter Components
  const allocatedFilterComponents = [
    <Select
      placeholder="Device"
      options={deviceOptions}
      value={allocatedFilters.device_id}
      onChange={(value) => setAllocatedFilters(prev => ({ ...prev, device_id: value }))}
      style={{ width: 150 }}
      suffixIcon={<LaptopOutlined />}
      allowClear
    />,
    <RangePicker
      value={[allocatedFilters.efficiency_factor_start, allocatedFilters.efficiency_factor_end]}
      onChange={(dates) => setAllocatedFilters(prev => ({ 
        ...prev, 
        efficiency_factor_start: dates ? dates[0] : null,
        efficiency_factor_end: dates ? dates[1] : null
      }))}
      allowClear={true}
      format="YYYY-MM-DD"
      placeholder={["Efficiency Start Date", "Efficiency End Date"]}
    />,
  ];

  // Storage Records Columns
  const storageColumns = [
    {
        title: <span style={{ color: "#80868B" }}>Record ID</span>,
        dataIndex: "id",
        key: "id",
        render: (id) => <span style={{ color: "#5F6368" }}>{id || "N/A"}</span>,
    },
    {
      title: <span style={{ color: "#80868B" }}>Device Name</span>,
      dataIndex: "device_id",
      key: "device_id",
      render: (id) => <span>{getDeviceName(id)}</span>,
      sorter: {
        compare: (a, b) => getDeviceName(a.device_id).localeCompare(getDeviceName(b.device_id)),
        multiple: 1,
      },
    },
    {
      title: <span style={{ color: "#80868B" }}>Flow Start</span>,
      dataIndex: "flow_start_datetime",
      key: "flow_start_datetime",
      render: (datetime) => (
        <span style={{ color: "#5F6368" }}>
          {new Date(datetime).toLocaleString()}
        </span>
      ),
      sorter: {
        compare: (a, b) => new Date(a.flow_start_datetime) - new Date(b.flow_start_datetime),
        multiple: 3,
      },
    },
    {
      title: <span style={{ color: "#80868B" }}>Flow End</span>,
      dataIndex: "flow_end_datetime",
      key: "flow_end_datetime",
      render: (datetime) => (
        <span style={{ color: "#5F6368" }}>
          {new Date(datetime).toLocaleString()}
        </span>
      ),
      sorter: {
        compare: (a, b) => new Date(a.flow_end_datetime) - new Date(b.flow_end_datetime),
        multiple: 4,
      },
    },
    {
      title: <span style={{ color: "#80868B" }}>Energy (MWh)</span>,
      dataIndex: "flow_energy",
      key: "flow_energy",
      render: (energy) => (energy / 1000000).toFixed(3), // Convert Wh to MWh
      sorter: {
        compare: (a, b) => a.flow_energy - b.flow_energy,
        multiple: 5,
      },
    },
    {
        title: <span style={{ color: "#80868B" }}>Flow Type</span>,
        dataIndex: "is_charging",
        key: "is_charging",
        render: (isCharging) => (
          <span style={{ color: isCharging ? "#34A853" : "#EA4335" }}>
            {isCharging ? "Charging" : "Discharging"}
          </span>
        ),
        sorter: {
          compare: (a, b) => a.is_charging - b.is_charging,
          multiple: 2,
        },
    },
  ];

  // Allocated Storage Records Columns
  const allocatedColumns = [
    {
      title: <span style={{ color: "#80868B" }}>Device Name</span>,
      dataIndex: "device_id",
      key: "device_id",
      render: (id) => <span>{getDeviceName(id)}</span>,
      sorter: {
        compare: (a, b) => getDeviceName(a.device_id).localeCompare(getDeviceName(b.device_id)),
        multiple: 1,
      },
    },
    {
      title: <span style={{ color: "#80868B" }}>GC Allocation ID</span>,
      dataIndex: "gc_allocation_id",
      key: "gc_allocation_id",
      render: (id) => <span style={{ color: "#5F6368" }}>{id || "N/A"}</span>,
    },
    {
      title: <span style={{ color: "#80868B" }}>SDGC Allocation ID</span>,
      dataIndex: "sdgc_allocation_id",
      key: "sdgc_allocation_id",
      render: (id) => <span style={{ color: "#5F6368" }}>{id || "N/A"}</span>,
    },
    {
      title: <span style={{ color: "#80868B" }}>SCR Allocation ID</span>,
      dataIndex: "scr_allocation_id",
      key: "scr_allocation_id",
      render: (id) => <span style={{ color: "#5F6368" }}>{id}</span>,
    },
    {
      title: <span style={{ color: "#80868B" }}>SDR Allocation ID</span>,
      dataIndex: "sdr_allocation_id",
      key: "sdr_allocation_id",
      render: (id) => <span style={{ color: "#5F6368" }}>{id}</span>,
    },
    {
      title: <span style={{ color: "#80868B" }}>SDR Proportion</span>,
      dataIndex: "sdr_proportion",
      key: "sdr_proportion",
      render: (proportion) => <span style={{ color: "#5F6368" }}>{(proportion * 100).toFixed(2)}%</span>,
      sorter: {
        compare: (a, b) => a.sdr_proportion - b.sdr_proportion,
        multiple: 2,
      },
    },
    {
      title: <span style={{ color: "#80868B" }}>Allocation Method</span>,
      dataIndex: "scr_allocation_methodology",
      key: "scr_allocation_methodology",
      render: (method) => <span style={{ color: "#5F6368" }}>{method}</span>,
    },
    {
      title: <span style={{ color: "#80868B" }}>Efficiency Factor</span>,
      dataIndex: "storage_efficiency_factor",
      key: "storage_efficiency_factor",
      render: (factor) => <span style={{ color: "#5F6368" }}>{(factor * 100).toFixed(2)}%</span>,
      sorter: {
        compare: (a, b) => a.storage_efficiency_factor - b.storage_efficiency_factor,
        multiple: 3,
      },
    },
  ];

  const handleStorageSelection = (selectedKeys, selectedRows) => {
    setStorageSelectedRowKeys(selectedKeys);
    setStorageSelectedRecords(selectedRows);
  };

  const handleAllocatedSelection = (selectedKeys, selectedRows) => {
    setAllocatedSelectedRowKeys(selectedKeys);
    setAllocatedSelectedRecords(selectedRows);
  };

  const handleApplyStorageFilter = () => {
    // Filter is applied automatically via useMemo
  };

  const handleClearStorageFilter = () => {
    setStorageFilters(defaultStorageFilters);
  };

  const handleApplyAllocatedFilter = () => {
    // Filter is applied automatically via useMemo
  };

  const handleClearAllocatedFilter = () => {
    setAllocatedFilters(defaultAllocatedFilters);
  };

  return (
    <>
      <FilterTable
        tableName="Storage Records"
        columns={storageColumns}
        filterComponents={storageFilterComponents}
        tableActionBtns={[]}
        defaultFilters={defaultStorageFilters}
        filters={storageFilters}
        dataSource={filteredStorageRecords}
        onRowsSelected={handleStorageSelection}
        handleApplyFilter={handleApplyStorageFilter}
        handleClearFilter={handleClearStorageFilter}
        selectedRowKeys={storageSelectedRowKeys}
        selectedRecords={storageSelectedRecords}
      />

      <div style={{ marginTop: "24px" }}>
        <FilterTable
          tableName="Allocated Storage Records"
          columns={allocatedColumns}
          filterComponents={allocatedFilterComponents}
          tableActionBtns={[]}
          defaultFilters={defaultAllocatedFilters}
          filters={allocatedFilters}
          dataSource={filteredAllocatedRecords}
          onRowsSelected={handleAllocatedSelection}
          handleApplyFilter={handleApplyAllocatedFilter}
          handleClearFilter={handleClearAllocatedFilter}
          selectedRowKeys={allocatedSelectedRowKeys}
          selectedRecords={allocatedSelectedRecords}
        />
      </div>
    </>
  );
};

export default Storage; 