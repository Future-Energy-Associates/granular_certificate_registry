/**
 * ValidationErrorDisplay Component
 *
 * A reusable component for displaying validation errors with expandable field details.
 * Can be used inline in forms or as part of error notifications.
 */

import React, { useState } from "react";
import { Alert, Collapse, Typography, Space, Tag } from "antd";
import {
  ExclamationCircleOutlined,
  DownOutlined,
  RightOutlined,
} from "@ant-design/icons";
import PropTypes from "prop-types";
import { formatFieldName, truncateValue } from "../../utils/errorUtils";

const { Text } = Typography;
const { Panel } = Collapse;

/**
 * Single error item display component.
 */
const ErrorItem = ({ error, showValue = true }) => {
  const fieldName = formatFieldName(error.field);
  const displayValue = truncateValue(error.invalid_value);

  return (
    <div
      style={{
        padding: "12px",
        backgroundColor: "#fff",
        borderRadius: "6px",
        marginBottom: "8px",
        border: "1px solid #ffccc7",
      }}
    >
      <Space direction="vertical" size={4} style={{ width: "100%" }}>
        <Space>
          <ExclamationCircleOutlined style={{ color: "#ff4d4f" }} />
          <Text strong style={{ color: "#262626" }}>
            {fieldName}
          </Text>
          {error.type && (
            <Tag
              color="error"
              style={{ fontSize: "11px", marginLeft: "8px" }}
            >
              {error.type}
            </Tag>
          )}
        </Space>

        <Text style={{ color: "#595959", display: "block" }}>
          {error.message}
        </Text>

        {showValue && displayValue !== "null" && (
          <div
            style={{
              backgroundColor: "#fafafa",
              padding: "6px 10px",
              borderRadius: "4px",
              fontFamily: "monospace",
              fontSize: "12px",
              color: "#8c8c8c",
              wordBreak: "break-all",
              marginTop: "4px",
            }}
          >
            <Text type="secondary">Received: </Text>
            <Text code>{displayValue}</Text>
          </div>
        )}

        {error.location && (
          <Text
            type="secondary"
            style={{ fontSize: "11px", display: "block", marginTop: "4px" }}
          >
            Location: {error.location}
          </Text>
        )}
      </Space>
    </div>
  );
};

ErrorItem.propTypes = {
  error: PropTypes.shape({
    field: PropTypes.string,
    message: PropTypes.string.isRequired,
    invalid_value: PropTypes.any,
    location: PropTypes.string,
    type: PropTypes.string,
  }).isRequired,
  showValue: PropTypes.bool,
};

/**
 * ValidationErrorDisplay - Main component for displaying validation errors.
 *
 * @param {Object} props
 * @param {string} props.message - Summary message to display
 * @param {Array} props.errors - Array of error objects from the API
 * @param {boolean} props.showValues - Whether to show invalid values
 * @param {boolean} props.collapsible - Whether the error list is collapsible
 * @param {boolean} props.defaultExpanded - Whether to expand by default
 * @param {string} props.type - Alert type (error, warning, info)
 * @param {Object} props.style - Additional styles
 */
const ValidationErrorDisplay = ({
  message = "Validation Error",
  errors = [],
  showValues = true,
  collapsible = true,
  defaultExpanded = true,
  type = "error",
  style = {},
}) => {
  const [expanded, setExpanded] = useState(defaultExpanded);

  if (!errors || errors.length === 0) {
    return (
      <Alert
        message={message}
        type={type}
        showIcon
        style={style}
      />
    );
  }

  const errorCount = errors.length;
  const summaryText =
    errorCount === 1
      ? "1 validation error"
      : `${errorCount} validation errors`;

  const errorList = (
    <div style={{ marginTop: "12px" }}>
      {errors.map((error, index) => (
        <ErrorItem key={index} error={error} showValue={showValues} />
      ))}
    </div>
  );

  if (!collapsible) {
    return (
      <Alert
        message={message}
        description={errorList}
        type={type}
        showIcon
        style={style}
      />
    );
  }

  return (
    <Alert
      message={
        <Space>
          <span>{message}</span>
          <Tag color="error">{summaryText}</Tag>
        </Space>
      }
      description={
        <div>
          <div
            onClick={() => setExpanded(!expanded)}
            style={{
              cursor: "pointer",
              color: "#1890ff",
              display: "flex",
              alignItems: "center",
              gap: "4px",
              marginBottom: expanded ? "8px" : 0,
              userSelect: "none",
            }}
          >
            {expanded ? <DownOutlined /> : <RightOutlined />}
            <span>{expanded ? "Hide details" : "Show details"}</span>
          </div>
          {expanded && errorList}
        </div>
      }
      type={type}
      showIcon
      style={style}
    />
  );
};

ValidationErrorDisplay.propTypes = {
  message: PropTypes.string,
  errors: PropTypes.arrayOf(
    PropTypes.shape({
      field: PropTypes.string,
      message: PropTypes.string.isRequired,
      invalid_value: PropTypes.any,
      location: PropTypes.string,
      type: PropTypes.string,
    })
  ),
  showValues: PropTypes.bool,
  collapsible: PropTypes.bool,
  defaultExpanded: PropTypes.bool,
  type: PropTypes.oneOf(["error", "warning", "info", "success"]),
  style: PropTypes.object,
};

/**
 * Compact version for use in smaller spaces or inline displays.
 */
export const ValidationErrorCompact = ({ errors = [], maxDisplay = 3 }) => {
  if (!errors || errors.length === 0) return null;

  const displayErrors = errors.slice(0, maxDisplay);
  const remaining = errors.length - maxDisplay;

  return (
    <div style={{ color: "#ff4d4f", fontSize: "13px" }}>
      {displayErrors.map((error, index) => (
        <div key={index} style={{ marginBottom: "4px" }}>
          <Text type="danger">
            <strong>{formatFieldName(error.field)}:</strong> {error.message}
          </Text>
        </div>
      ))}
      {remaining > 0 && (
        <Text type="secondary" style={{ fontSize: "12px" }}>
          ...and {remaining} more error{remaining > 1 ? "s" : ""}
        </Text>
      )}
    </div>
  );
};

ValidationErrorCompact.propTypes = {
  errors: PropTypes.array,
  maxDisplay: PropTypes.number,
};

export default ValidationErrorDisplay;
