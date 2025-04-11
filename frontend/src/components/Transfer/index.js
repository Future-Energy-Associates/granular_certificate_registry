import React, { useState, useMemo, useEffect, useRef } from "react";
import dayjs from "dayjs";
import Cookies from "js-cookie";
import * as styles from "../Certificate/Certificate.module.css";

import { Button, Card, Col, Divider, message, Select, DatePicker } from "antd";

import {
  SwapOutlined,
  CloseOutlined,
  DownloadOutlined,
  LaptopOutlined,
  ThunderboltOutlined,
  ClockCircleOutlined,
} from "@ant-design/icons";

import "../../assets/styles/pagination.css";
import "../../assets/styles/filter.css";
import certificateTotal from "../../assets/images/certificate-total.png";
import certificateTransferred from "../../assets/images/certificate-transferred.png";
import certificateCancelled from "../../assets/images/certificate-cancelled.png";

import { useDispatch, useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import { useAccount } from "../../context/AccountContext";
import {
  fetchCertificates,
  getCertificateDetails,
} from "../../store/certificate/certificateThunk";

import CertificateActionDialog from "../Certificate/CertificateActionDialog";
import CertificateDetailDialog from "../Certificate/CertificateDetailDialog";

import StatusTag from "../common/StatusTag";

import FilterTable from "../common/FilterTable";

import {
  CERTIFICATE_STATUS,
  ENERGY_SOURCE,
  DEVICE_TECHNOLOGY_TYPE,
} from "../../enum";

import { isEmpty } from "../../utils";

const { Option } = Select;
const { RangePicker } = DatePicker;

const Transfer = () => {
  const { currentAccount } = useAccount();

  const dispatch = useDispatch();
  const navigate = useNavigate();

  const { certificates } = useSelector((state) => state.certificates);

  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [selectedCertificateData, setSelectedCertificateData] = useState(null);

  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [selectedRecords, setSelectedRecords] = useState([]);
  const [dialogAction, setDialogAction] = useState(null);
  const [totalProduction, setTotalProduction] = useState(null);
  const [selectedDevices, setSelectedDevices] = useState([]);

  const dialogRef = useRef();

  const userInfo = JSON.parse(Cookies.get("user_data")).userInfo;

  const deviceOptions = useMemo(() => {
    const allDevices = [
      ...(currentAccount?.detail?.devices || []),
      ...(currentAccount?.detail?.certificateDevices || []),
    ];

    console.log("all DEVICES", allDevices);

    const uniqueDevices = Array.from(
      new Map(allDevices.map((device) => [device.id, device])).values()
    );

    return uniqueDevices.map((device) => ({
      value: device.id,
      label: device.device_name || `Device ${device.id}`,
    }));
  }, [
    currentAccount?.detail?.devices,
    currentAccount?.detail?.certificateDevices,
  ]);

  const today = dayjs();
  const one_month_ago = dayjs().subtract(30, "days");

  const defaultFilters = {
    device_id: null,
    energy_source: null,
    certificate_bundle_status: CERTIFICATE_STATUS.active,
    certificate_period_start: dayjs(one_month_ago),
    certificate_period_end: dayjs(today),
  };

  const [filters, setFilters] = useState(defaultFilters);

  useEffect(() => {
    setFilters((prevFilters) => ({
      ...prevFilters,
      certificate_period_start: one_month_ago,
      certificate_period_end: today,
    }));
  }, []);

  useEffect(() => {
    if (!dialogAction) return;

    dialogRef.current.openDialog(); // Open the dialog from the parent component
  }, [dialogAction]);

  useEffect(() => {
    if (currentAccount && !currentAccount?.detail.id) {
      navigate("/login");
      return;
    }
  }, [currentAccount, navigate]);

  useEffect(() => {
    if (!currentAccount?.detail.id) return;

    fetchCertificatesData();
  }, [currentAccount, dispatch]);

  useEffect(() => {
    if (isEmpty(filters) && currentAccount?.detail.id) {
      fetchCertificatesData();
    }
  }, [filters]);

  useEffect(() => {
    const totalProduction = selectedRecords.reduce(
      (sum, record) => sum + record.bundle_quantity,
      0
    );
    const devices = selectedRecords.reduce((acc, newDevice) => {
      const isDuplicate = acc.some((device) => device === newDevice.device_id);
      return isDuplicate ? acc : [...acc, newDevice.device_id];
    }, []);
    setTotalProduction(totalProduction);
    setSelectedDevices(devices);
  }, [selectedRecords]);

  // Get top 3 devices with the highest quantity in summary
  // Convert object to array of [key, value] pairs, sort by value, and get top 3
  const topThreeDevices = Object.entries(
    currentAccount?.summary.num_devices_by_type || {}
  )
    .sort((a, b) => b[1] - a[1]) // Sort by value (second element of the array)
    .slice(0, 3) // Get the top 3
    .map(([type, count]) => ({ type, count })); // Convert back to an array of object

  const fetchCertificatesData = async () => {
    const fetchBody = {
      user_id: userInfo.userID,
      source_id: currentAccount?.detail.id,
      device_id: filters.device_id,
      certificate_bundle_status:
        CERTIFICATE_STATUS[filters.certificate_bundle_status], // Transform status to match API expectations
      certificate_period_start:
        filters.certificate_period_start?.format("YYYY-MM-DD"),
      certificate_period_end:
        filters.certificate_period_end?.format("YYYY-MM-DD"),
      energy_source: filters.energy_source,
    };
    try {
      await dispatch(fetchCertificates(fetchBody)).unwrap();
    } catch (error) {
      console.error("Failed to fetch certificates:", error);
      message.error(error?.message || "Failed to fetch certificates");
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const handleApplyFilter = () => {
    fetchCertificatesData();
  };

  const handleGetCertificateDetail = async (certificateId) => {
    try {
      const response = await dispatch(
        getCertificateDetails(certificateId)
      ).unwrap();
      setSelectedCertificateData(response);
      setIsDetailModalOpen(true);
    } catch (error) {
      message.error(error?.message || "Failed to fetch certificate details");
    }
  };

  const handleClearFilter = async () => {
    setFilters({});
  };

  const getDeviceName = (deviceID) => {
    return (
      currentAccount?.detail.devices.find((device) => deviceID === device.id)
        ?.device_name || `Device ${deviceID}`
    );
  };

  const handleDateChange = (dates) => {
    setFilters((prev) => ({
      ...prev,
      certificate_period_start: dates[0],
      certificate_period_end: dates[1],
    }));
  };

  const onSelectChange = (newSelectedRowKeys, newSelectedRows) => {
    setSelectedRowKeys(newSelectedRowKeys);
    setSelectedRecords(newSelectedRows);
  };

  const openDialog = (action) => {
    setDialogAction(action);
  };

  const closeDialog = () => {
    dialogRef.current.closeDialog(); // Close the dialog from the parent component
  };

  const isCertificatesSelected = selectedRowKeys.length > 0;

  const btnList = useMemo(
    () => [
      {
        icon: <CloseOutlined />,
        btnType: "primary",
        type: "cancel",
        disabled: !isCertificatesSelected,
        style: { height: "40px" },
        name: "Cancel",
        handle: () => openDialog("cancel"),
      },
      {
        icon: <DownloadOutlined />,
        btnType: "primary",
        type: "reserve",
        disabled: true,
        style: { height: "40px" },
        name: "Reserve",
        handle: () => openDialog("reserve"),
      },
      {
        icon: <SwapOutlined />,
        btnType: "primary",
        type: "transfer",
        disabled: !isCertificatesSelected,
        style: { height: "40px" },
        name: "Transfer",
        handle: () => openDialog("transfer"),
      },
    ],
    [isCertificatesSelected]
  );

  const filterComponents = [
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
    /* Energy Source Filter */
    <Select
      placeholder="Energy Source"
      value={filters.energy_source}
      onChange={(value) => handleFilterChange("energy_source", value)}
      style={{ width: 150 }}
      suffixIcon={<ThunderboltOutlined />}
      allowClear
    >
      {Object.entries(ENERGY_SOURCE).map(([key, value]) => (
        <Option key={key} value={key.toLocaleLowerCase()}>
          {value}
        </Option>
      ))}
    </Select>,
    /* Date range Filter */
    <RangePicker
      value={[filters.certificate_period_start, filters.certificate_period_end]}
      onChange={(dates) => handleDateChange(dates)}
      allowClear={false}
      format="YYYY-MM-DD"
    />,
    <Select
      // mode="multiple"
      placeholder="Status"
      value={filters.status}
      onChange={(value) =>
        handleFilterChange("certificate_bundle_status", value)
      }
      style={{ width: 200 }}
      allowClear
      suffixIcon={<ClockCircleOutlined />}
    >
      {Object.entries(CERTIFICATE_STATUS).map(([key, value]) => (
        <Option key={key} value={key}>
          {value}
        </Option>
      ))}
    </Select>,
  ];

  const columns = [
    {
      title: <span style={{ color: "#80868B" }}>Issuance ID</span>,
      dataIndex: "issuance_id",
      key: "issuance_id",
    },
    {
      title: <span style={{ color: "#80868B" }}>Device Name</span>,
      dataIndex: "device_id",
      key: "device_id",
      render: (id) => <span>{getDeviceName(id)}</span>,
    },
    {
      title: <span style={{ color: "#80868B" }}>Energy Source</span>,
      dataIndex: "energy_source",
      key: "energy_source",
      render: (text) => (
        <span style={{ color: "#5F6368" }}>
          {text.charAt(0).toUpperCase() + text.slice(1)}
        </span>
      ),
    },
    {
      title: <span style={{ color: "#80868B" }}>Certificate Period Start</span>,
      dataIndex: "production_starting_interval",
      key: "production_starting_interval",
      render: (text) => <span style={{ color: "#5F6368" }}>{text}</span>,
    },
    {
      title: <span style={{ color: "#80868B" }}>Certificate Period End</span>,
      dataIndex: "production_ending_interval",
      key: "production_ending_interval",
      render: (text) => <span style={{ color: "#5F6368" }}>{text}</span>,
    },
    {
      title: <span style={{ color: "#80868B" }}>Production (MWh)</span>,
      dataIndex: "bundle_quantity",
      key: "bundle_quantity",
      render: (value) => (value / 1e6).toFixed(3), // Divides by 1,000,000 and shows 3 decimal places
    },
    {
      title: <span style={{ color: "#80868B" }}>Status</span>,
      dataIndex: "certificate_bundle_status",
      key: "certificate_bundle_status",
      render: (status) => <StatusTag status={String(status || "")} />, // Ensure status is a string
    },
    {
      title: "",
      render: (_, record) => {
        return (
          <Button
            style={{ color: "#043DDC", fontWeight: "600" }}
            type="link"
            onClick={() => handleGetCertificateDetail(record.id)}
          >
            Details
          </Button>
        );
      },
    },
  ];

  const summary = (
    <>
      {" "}
      <Col span={12}>
        <Card className={styles["card-wrapper"]}>
          <div className={styles["card-body"]}>
            <img className={styles["icon-img"]} src={certificateTotal} />
            <div className={styles["information-container"]}>
              <h3 className={styles["summary-value"]}>
                {currentAccount?.summary.num_granular_certificate_bundles ||
                  "0"}
              </h3>
              <p className={styles["summary-text"]}>Total Certificates</p>
            </div>
            <Divider
              type="vertical"
              style={{ height: "50px", margin: "0", color: "#DADCE0" }}
            />
            {topThreeDevices.map((deviceQuantity) => (
              <div className={styles["top-device-container"]}>
                <h3 className={styles["summary-value"]}>
                  {deviceQuantity.count || "0"}
                </h3>
                <p className={styles["summary-text"]}>
                  {DEVICE_TECHNOLOGY_TYPE[deviceQuantity.type.toUpperCase()]}
                </p>
              </div>
            ))}
          </div>
        </Card>
      </Col>
      <Col span={6}>
        <Card className={styles["card-wrapper"]}>
          <div className={styles["card-body"]}>
            <img className={styles["icon-img"]} src={certificateTransferred} />
            <div className={styles["information-container"]}>
              <h3 className={styles["summary-value"]}>
                {Math.floor(
                  currentAccount?.summary.num_granular_certificate_bundles *
                    0.25
                ) || "0"}
              </h3>
              <p className={styles["summary-text"]}>Certificates Transferred</p>
            </div>
          </div>
        </Card>
      </Col>
      <Col span={6}>
        <Card className={styles["card-wrapper"]}>
          <div className={styles["card-body"]}>
            <img className={styles["icon-img"]} src={certificateCancelled} />
            <div className={styles["information-container"]}>
              <h3 className={styles["summary-value"]}>
                {currentAccount?.summary
                  .num_cancelled_granular_certificate_bundles || "0"}
              </h3>
              <p className={styles["summary-text"]}>Certificates Cancelled</p>
            </div>
          </div>
        </Card>
      </Col>
    </>
  );

  return (
    <>
      <FilterTable
        summary={summary}
        tableName="Transfer history"
        columns={columns}
        filterComponents={filterComponents}
        tableActionBtns={btnList}
        defaultFilters={defaultFilters}
        filters={filters}
        dataSource={certificates}
        fetchTableData={fetchCertificatesData}
        onRowsSelected={onSelectChange}
        handleApplyFilter={handleApplyFilter}
        handleClearFilter={handleClearFilter}
      />

      {/* Dialog component with a ref to control it from outside */}
      <CertificateActionDialog
        dialogAction={dialogAction}
        selectedRowKeys={selectedRowKeys}
        ref={dialogRef}
        totalProduction={totalProduction}
        selectedDevices={selectedDevices}
        updateCertificateActionDialog={setDialogAction}
        getDeviceName={getDeviceName}
        fetchCertificatesData={fetchCertificatesData}
        setSelectedRowKeys={setSelectedRowKeys}
        getCertificateDetail={handleGetCertificateDetail}
      />
      <CertificateDetailDialog
        open={isDetailModalOpen}
        onClose={() => setIsDetailModalOpen(false)}
        certificateData={selectedCertificateData}
      />
    </>
  );
};

export default Transfer;
