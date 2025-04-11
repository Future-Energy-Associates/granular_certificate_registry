import { Tag } from "antd";
import React from "react";

// Custom Status Colors
const statusColors = {
  claimed: "#1D53F7", // Blue
  retired: "#80868B", // Gray
  active: "#12B76A", // Green
  expired: "#D92D20", // Red
  locked: "#D92D20", // Red (Same as Expired)
  withdraw: "#F79009", // Orange
  reserved: "#F79009", // Orange (Same as Withdraw)
};

// Status Tag Style
const StatusTag = ({ status }) => {
  const normalizedStatus = (status || "").toLowerCase();

  return (
    <Tag
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: "0 10px",
        height: "28px",
        border: `1px solid #D0D5DD`,
        backgroundColor: "#fff",
      }}
    >
      <span
        style={{
          display: "inline-block",
          width: "8px",
          height: "8px",
          borderRadius: "50%",
          backgroundColor: statusColors[normalizedStatus] || "#80868B", // Fallback color
          marginRight: "8px",
        }}
      />
      <span style={{ color: "#5F6368", fontWeight: "500" }}>
        {status || "Unknown"} {/* Add fallback text */}
      </span>
    </Tag>
  );
};

export default StatusTag;
