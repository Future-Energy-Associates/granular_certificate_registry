import React from "react";
import { Modal, Typography, Divider, Space } from "antd";
import StatusTag from "../common/StatusTag";

const { Text } = Typography;

const DataRow = ({ label, value, color }) => (
  <div
    style={{
      display: "flex",
      alignItems: "center",
      minHeight: "24px",
      width: "100%",
    }}
  >
    <Text
      style={{
        width: "200px",
        color: "#80868B",
        fontWeight: 500,
        fontSize: "14px",
        lineHeight: "20px",
      }}
    >
      {label}
    </Text>
    <Text
      style={{
        flex: 1,
        marginLeft: "24px",
        color: color || "#202124",
        fontWeight: 500,
        fontSize: "14px",
        lineHeight: "20px",
      }}
    >
      {value}
    </Text>
  </div>
);

const SectionTitle = ({ children }) => (
  <Text
    style={{
      color: "#344054",
      fontWeight: 600,
      fontSize: "14px",
      lineHeight: "20px",
    }}
  >
    {children}
  </Text>
);

const CertificateDetailDialog = ({ open, onClose, certificateData }) => {
  if (!certificateData) return null;

  const certificateDetails = [
    {
      label: "Certificate Bundle Status",
      value: <StatusTag status={certificateData.certificate_bundle_status} />,
    },
    { label: "Account", value: certificateData.account_id },
    { label: "Device name", value: certificateData.device_name },
    {
      label: "Certificate bundle id range start",
      value: certificateData.certificate_bundle_id_range_start,
    },
    {
      label: "Certificate bundle id range end",
      value: certificateData.certificate_bundle_id_range_end,
    },
    { label: "Bundle quantity", value: certificateData.bundle_quantity },
    { label: "Issuance id", value: certificateData.issuance_id },
    { label: "Energy carrier", value: certificateData.energy_source },
    {
      label: "Issuance post energy carrier conversion",
      value: "True",
      color: "#039855",
    },
  ];

  const deviceDetails = [
    { label: "Device id", value: certificateData.device_id },
    { label: "Device name", value: certificateData.device_name },
    { label: "Device technology type", value: certificateData.energy_source },
    {
      label: "Device production start date",
      value: certificateData.production_start_time,
    },
    {
      label: "Device capacity",
      value: `${certificateData.device_capacity || 5000000} (MegaWatts)`,
    },
    {
      label: "Device location",
      value: certificateData.device_location || "(51.5074, -0.1278)",
    },
    { label: "Device type", value: certificateData.energy_source },
  ];

  const issuingDetails = [
    {
      label: "Country of issuance",
      value: certificateData.country || "United States",
    },
    {
      label: "Connected grid identification",
      value: certificateData.grid_id || "ZoneA1",
    },
    {
      label: "Issuing body",
      value: certificateData.issuing_body || "UK Renewable Energy Authority",
    },
    { label: "Legal status", value: "Regulated Entity" },
    { label: "Issuance purpose", value: "Disclosure" },
    { label: "Support received", value: "Government Grant" },
    { label: "Quality scheme reference", value: "ISO14001" },
    { label: "Dissemination level", value: "Self-consumed" },
    {
      label: "Issue market zone",
      value: certificateData.market_id || "UK-BM-001",
    },
  ];

  return (
    <Modal
      title="Certificate Details"
      open={open}
      onCancel={onClose}
      width={640}
      footer={null}
    >
      <Space
        direction="vertical"
        size={12}
        style={{ width: "100%", padding: "24px" }}
      >
        <SectionTitle>Certificates details</SectionTitle>
        {certificateDetails.map((item, index) => (
          <DataRow key={index} {...item} />
        ))}

        <Divider style={{ margin: "12px 0" }} />

        <SectionTitle>Production device details</SectionTitle>
        {deviceDetails.map((item, index) => (
          <DataRow key={index} {...item} />
        ))}

        <Divider style={{ margin: "12px 0" }} />

        <SectionTitle>Issuing body details</SectionTitle>
        {issuingDetails.map((item, index) => (
          <DataRow key={index} {...item} />
        ))}
      </Space>
    </Modal>
  );
};

export default CertificateDetailDialog;
