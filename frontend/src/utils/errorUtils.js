/**
 * Error utilities for formatting and displaying validation errors.
 *
 * This module provides utilities for working with structured API error responses
 * and displaying them to users via Ant Design notifications.
 */

import { notification } from "antd";
import React from "react";

/**
 * Format a field name for display (convert snake_case to Title Case).
 *
 * @param {string} fieldName - The field name to format
 * @returns {string} Formatted field name
 */
export const formatFieldName = (fieldName) => {
  if (!fieldName) return "Unknown field";

  return fieldName
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
};

/**
 * Truncate a value for display if it's too long.
 *
 * @param {any} value - The value to truncate
 * @param {number} maxLength - Maximum length before truncation
 * @returns {string} Truncated string representation
 */
export const truncateValue = (value, maxLength = 50) => {
  if (value === null || value === undefined) return "null";

  const strValue = typeof value === "object" ? JSON.stringify(value) : String(value);

  if (strValue.length > maxLength) {
    return strValue.substring(0, maxLength - 3) + "...";
  }

  return strValue;
};

/**
 * Format a single validation error for display.
 *
 * @param {Object} error - The error object from the API
 * @param {string} error.field - Field name
 * @param {string} error.message - Error message
 * @param {any} error.invalid_value - The invalid value
 * @param {string} error.location - Full location path
 * @returns {Object} Formatted error object
 */
export const formatValidationError = (error) => {
  return {
    field: formatFieldName(error.field),
    message: error.message,
    value: truncateValue(error.invalid_value),
    location: error.location,
    type: error.type,
  };
};

/**
 * Get a user-friendly summary message based on error type.
 *
 * @param {string} errorType - The error type from the API
 * @param {number} errorCount - Number of errors (for validation errors)
 * @returns {string} User-friendly summary message
 */
export const getErrorSummary = (errorType, errorCount = 0) => {
  switch (errorType) {
    case "validation_error":
      return errorCount === 1
        ? "There was a validation error with your request"
        : `There were ${errorCount} validation errors with your request`;
    case "http_error":
      return "The request could not be completed";
    case "server_error":
      return "An internal server error occurred";
    case "network_error":
      return "Unable to connect to the server";
    default:
      return "An error occurred";
  }
};

/**
 * Create the description content for a validation error notification.
 *
 * @param {Array} errors - Array of validation errors
 * @returns {React.ReactNode} React element for the notification description
 */
const createValidationErrorDescription = (errors) => {
  const formattedErrors = errors.map(formatValidationError);

  return React.createElement(
    "div",
    { style: { maxHeight: "300px", overflowY: "auto" } },
    formattedErrors.map((error, index) =>
      React.createElement(
        "div",
        {
          key: index,
          style: {
            marginBottom: index < formattedErrors.length - 1 ? "12px" : 0,
            paddingBottom: index < formattedErrors.length - 1 ? "12px" : 0,
            borderBottom:
              index < formattedErrors.length - 1
                ? "1px solid #f0f0f0"
                : "none",
          },
        },
        React.createElement(
          "div",
          {
            style: {
              fontWeight: 600,
              color: "#262626",
              marginBottom: "4px",
            },
          },
          error.field
        ),
        React.createElement(
          "div",
          {
            style: {
              color: "#595959",
              fontSize: "13px",
              marginBottom: "4px",
            },
          },
          error.message
        ),
        error.value !== "null" &&
          React.createElement(
            "div",
            {
              style: {
                color: "#8c8c8c",
                fontSize: "12px",
                fontFamily: "monospace",
                backgroundColor: "#fafafa",
                padding: "4px 8px",
                borderRadius: "4px",
                wordBreak: "break-all",
              },
            },
            `Value: ${error.value}`
          )
      )
    )
  );
};

/**
 * Display a validation error notification with expandable field details.
 *
 * @param {Object} error - The parsed error object from baseAPI
 * @param {string} error.message - Error message
 * @param {Array} error.errors - Array of field-level errors
 * @param {string} error.errorType - Type of error
 * @param {Object} options - Additional notification options
 */
export const showValidationError = (error, options = {}) => {
  const { errors = [], errorType = "validation_error", message } = error;
  const errorCount = errors.length;

  notification.error({
    message: message || getErrorSummary(errorType, errorCount),
    description:
      errorCount > 0 ? createValidationErrorDescription(errors) : null,
    duration: errorCount > 3 ? 0 : 8, // Don't auto-close if many errors
    placement: "topRight",
    style: {
      width: 420,
    },
    ...options,
  });
};

/**
 * Display an HTTP error notification.
 *
 * @param {Object} error - The parsed error object from baseAPI
 * @param {Object} options - Additional notification options
 */
export const showHttpError = (error, options = {}) => {
  const { message, status } = error;

  notification.error({
    message: `Error ${status}`,
    description: message || "The request could not be completed",
    duration: 6,
    placement: "topRight",
    ...options,
  });
};

/**
 * Display a server error notification.
 *
 * @param {Object} error - The parsed error object from baseAPI
 * @param {Object} options - Additional notification options
 */
export const showServerError = (error, options = {}) => {
  notification.error({
    message: "Server Error",
    description:
      error.message || "An internal server error occurred. Please try again later.",
    duration: 8,
    placement: "topRight",
    ...options,
  });
};

/**
 * Display an appropriate error notification based on the error type.
 * This is the main entry point for displaying API errors.
 *
 * @param {Object} error - The parsed error object from baseAPI
 * @param {Object} options - Additional notification options
 */
export const showApiError = (error, options = {}) => {
  if (!error) {
    notification.error({
      message: "Error",
      description: "An unexpected error occurred",
      duration: 6,
      placement: "topRight",
      ...options,
    });
    return;
  }

  const { errorType, isValidationError } = error;

  if (isValidationError || errorType === "validation_error") {
    showValidationError(error, options);
  } else if (errorType === "http_error") {
    showHttpError(error, options);
  } else if (errorType === "server_error") {
    showServerError(error, options);
  } else {
    // Fallback for unknown error types
    notification.error({
      message: "Error",
      description: error.message || "An unexpected error occurred",
      duration: 6,
      placement: "topRight",
      ...options,
    });
  }
};

/**
 * Extract a simple error message from a parsed error object.
 * Useful for displaying in message.error() or simple text displays.
 *
 * @param {Object} error - The parsed error object from baseAPI
 * @returns {string} Simple error message
 */
export const getSimpleErrorMessage = (error) => {
  if (!error) return "An unexpected error occurred";

  if (error.isValidationError && error.errors?.length > 0) {
    const firstError = error.errors[0];
    return `${formatFieldName(firstError.field)}: ${firstError.message}`;
  }

  return error.message || "An unexpected error occurred";
};
