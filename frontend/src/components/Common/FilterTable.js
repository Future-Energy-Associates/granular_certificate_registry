import React, { useState, useEffect } from "react";

import {
  Table,
  Button,
  Row,
  Space,
  Divider,
  Flex,
  Pagination,
  Layout,
  Typography,
} from "antd";

import { LeftOutlined, RightOutlined } from "@ant-design/icons";

import { useDispatch } from "react-redux";

const { Content } = Layout;
const { Text } = Typography;

const FilterTable = ({
  summary,
  tableName,
  columns,
  filterComponents,
  tableActionBtns,
  defaultFilters,
  filters,
  tableThunks,
  dataSource,
  fetchTableData,
  onRowsSelected,
  handleApplyFilter,
  handleClearFilter,
  isShowSelection = true,
  selectedRowKeys = [],
  selectedRecords = [],
}) => {
  const dispatch = useDispatch();
  const [currentPage, setCurrentPage] = useState(1);
  
  // Internal state to manage cross-page selections
  const [allSelectedRowKeys, setAllSelectedRowKeys] = useState(new Set(selectedRowKeys));
  const [allSelectedRecords, setAllSelectedRecords] = useState(new Map());

  const pageSize = 10;

  // Initialize selected records map when selectedRecords prop changes
  useEffect(() => {
    if (selectedRecords && selectedRecords.length > 0) {
      const recordsMap = new Map();
      selectedRecords.forEach(record => {
        recordsMap.set(record.id, record);
      });
      setAllSelectedRecords(recordsMap);
    }
  }, [selectedRecords]);

  // Sync internal state with external selectedRowKeys
  useEffect(() => {
    setAllSelectedRowKeys(new Set(selectedRowKeys));
  }, [selectedRowKeys]);

  // useEffect(() => {
  //   if (fetchTableData) fetchTableData();
  // }, [filters, dispatch]);

  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const totalPages = Math.ceil(dataSource?.length / pageSize);

  // Get current page data
  const currentPageData = dataSource?.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  // Filter selected keys to only include those visible on current page
  const currentPageSelectedKeys = currentPageData
    ?.filter(record => allSelectedRowKeys.has(record.id))
    ?.map(record => record.id) || [];

  // Handler to clear all selections across all pages
  const handleClearAllSelections = () => {
    setAllSelectedRowKeys(new Set());
    setAllSelectedRecords(new Map());
    
    // Call parent callback with empty arrays
    if (onRowsSelected) {
      onRowsSelected([], []);
    }
  };

  // Handler to select/deselect all rows on current page
  const handleToggleCurrentPageSelection = () => {
    const currentPageIds = currentPageData?.map(record => record.id) || [];
    const allCurrentPageSelected = currentPageIds.every(id => allSelectedRowKeys.has(id));
    
    const newSelectedKeys = new Set(allSelectedRowKeys);
    const newSelectedRecords = new Map(allSelectedRecords);
    
    if (allCurrentPageSelected) {
      // Deselect all on current page
      currentPageIds.forEach(id => {
        newSelectedKeys.delete(id);
        newSelectedRecords.delete(id);
      });
    } else {
      // Select all on current page
      currentPageData?.forEach(record => {
        newSelectedKeys.add(record.id);
        newSelectedRecords.set(record.id, record);
      });
    }
    
    setAllSelectedRowKeys(newSelectedKeys);
    setAllSelectedRecords(newSelectedRecords);
    
    // Call parent callback
    if (onRowsSelected) {
      const allSelectedKeysArray = Array.from(newSelectedKeys);
      const allSelectedRecordsArray = Array.from(newSelectedRecords.values());
      onRowsSelected(allSelectedKeysArray, allSelectedRecordsArray);
    }
  };

  const rowSelection = {
    selectedRowKeys: currentPageSelectedKeys,
    onChange: (selectedKeys, selectedRows) => {
      // Create new sets/maps to avoid mutation
      const newSelectedKeys = new Set(allSelectedRowKeys);
      const newSelectedRecords = new Map(allSelectedRecords);
      
      // Get current page row IDs
      const currentPageIds = new Set(currentPageData?.map(record => record.id) || []);
      
      // Remove all current page selections first
      currentPageIds.forEach(id => {
        newSelectedKeys.delete(id);
        newSelectedRecords.delete(id);
      });
      
      // Add new selections from current page
      selectedKeys.forEach(key => {
        newSelectedKeys.add(key);
      });
      
      selectedRows.forEach(row => {
        newSelectedRecords.set(row.id, row);
      });
      
      // Update internal state
      setAllSelectedRowKeys(newSelectedKeys);
      setAllSelectedRecords(newSelectedRecords);
      
      // Call parent callback with all selected data
      if (onRowsSelected) {
        const allSelectedKeysArray = Array.from(newSelectedKeys);
        const allSelectedRecordsArray = Array.from(newSelectedRecords.values());
        onRowsSelected(allSelectedKeysArray, allSelectedRecordsArray);
      }
    },
    onSelectAll: (selected, selectedRows, changeRows) => {
      // Override the default select all behavior to work with our cross-page logic
      handleToggleCurrentPageSelection();
    },
  };

  const isEmpty = (obj) => {
    return Object.keys(obj).length === 0;
  };

  // Go to Previous Page
  const handlePrev = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  // Go to Next Page
  const handleNext = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    }
  };

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  return (
    <Content style={{ margin: "24px" }}>
      <Row gutter={16}>{summary}</Row>

      <Flex
        style={{
          justifyContent: "space-between",
          alignItems: "center",
          backgroundColor: "#fff",
          padding: "12px",
          border: "1px solid #f0f0f0",
          borderRadius: "8px 8px 0 0",
          marginTop: "12px",
        }}
      >
        <Text style={{ color: "#344054", fontWeight: "500", fontSize: "20px" }}>
          {tableName}
        </Text>
        <Space>

          {/* Clear All Selections Button - only show when there are selections */}
          {allSelectedRowKeys.size > 0 && (
            <Button
              type="text"
              onClick={handleClearAllSelections}
              style={{
                color: "#ff4d4f",
                fontWeight: "500",
                fontSize: "12px",
              }}
              size="small"
            >
              Clear All
            </Button>
          )}

          {/* Select/Deselect Current Page Button */}
          {isShowSelection && currentPageData && currentPageData.length > 0 && (
            <><Button
              type="text"
              onClick={handleToggleCurrentPageSelection}
              style={{
                color: "#043DDC",
                fontWeight: "500",
                fontSize: "12px",
              }}
              size="small"
            >
              {currentPageData.every(record => allSelectedRowKeys.has(record.id))
                ? "Deselect Page"
                : "Select Page"}
            </Button>
            
           <Text
              style={{
                color: "#202124",
                fontWeight: "500",
                display: allSelectedRowKeys.size < 1 ? "none" : "inline",
              }}
            >
                ({allSelectedRowKeys.size} selected)
            </Text></>
          )}

          {tableActionBtns &&
            tableActionBtns.map((action, index) => {
              return (
                <Button
                  icon={action.icon}
                  type={action.btnType}
                  disabled={action.disabled}
                  style={action.style}
                  onClick={() => action.handle()}
                  key={index}
                >
                  {action.name}
                </Button>
              );
            })}
        </Space>
      </Flex>
      <Space
        style={{
          width: "100%",
          padding: "8px 16px",
          backgroundColor: "#fff",
          borderBottom: "1px solid #EAECF0",
        }}
        split={<Divider type="vertical" />}
      >
        {filterComponents &&
          filterComponents.map((component, index) => (
            <div key={index}>{component}</div>
          ))}
        {/* Apply Filter Button */}
        <Button
          type="link"
          onClick={() => handleApplyFilter()}
          style={{ color: "#043DDC", fontWeight: "600" }}
        >
          Apply filter
        </Button>

        {/* Clear Filter Button */}
        <Button
          type="text"
          onClick={() => handleClearFilter()}
          disabled={isEmpty(filters) ? true : false}
          style={{
            color: isEmpty(filters) ? "#DADCE0" : "#5F6368",
            fontWeight: "600",
          }}
        >
          Clear Filter
        </Button>
      </Space>
      <Table
        style={{
          borderRadius: "0 0 8px 8px",
          fontWeight: "500",
          color: "#F9FAFB",
        }}
        rowSelection={isShowSelection && rowSelection}
        columns={columns}
        dataSource={currentPageData}
        rowKey="id"
        pagination={false}
      />
      <Flex className="pagination-container">
        {/* Previous Button */}
        <Button
          icon={<LeftOutlined />}
          onClick={handlePrev}
          disabled={currentPage === 1}
          className={`pagination-btn ${currentPage === 1 ? "disabled" : ""}`}
        >
          Previous
        </Button>

        {/* Custom Pagination */}
        <Pagination
          className="custom-paging"
          current={currentPage}
          total={dataSource?.length}
          pageSize={pageSize}
          onChange={handlePageChange}
          showSizeChanger={false}
          itemRender={(page, type, originalElement) => {
            if (type === "prev" || type === "next") {
              return null; // Remove default arrows
            }

            if (type === "page") {
              return (
                <div
                  onClick={() => handlePageChange(page)}
                  className={`pagination-number ${
                    page === currentPage ? "active" : ""
                  }`}
                >
                  {page}
                </div>
              );
            }
            return originalElement;
          }}
        />

        {/* Next Button */}
        <Button
          icon={<RightOutlined />}
          onClick={handleNext}
          disabled={currentPage === totalPages}
          className={`pagination-btn ${
            currentPage === totalPages ? "disabled" : ""
          }`}
        >
          Next
        </Button>
      </Flex>
    </Content>
  );
};

export default FilterTable;
