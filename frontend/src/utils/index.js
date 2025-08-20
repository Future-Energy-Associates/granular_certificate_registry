import Cookies from "js-cookie";

export const saveDataToCookies = (key, data, options = { expires: 7 }) => {
  Cookies.set(key, data, options);
};

export const getCookies = (key) => {
  return Cookies.get(key);
};

export const removeCookies = (key) => {
  Cookies.remove(key);
};

export const removeAllCookies = () => {
  // Get all cookies
  const allCookies = Cookies.get(); // This returns an object of all cookies

  // Iterate over each cookie and remove it
  for (const cookieName in allCookies) {
    if (allCookies.hasOwnProperty(cookieName)) {
      Cookies.remove(cookieName); // Remove each cookie by name
    }
  }
};

// Save data to sessionStorage with size check
export const saveDataToSessionStorage = (key, data) => {
  sessionStorage.setItem(key, JSON.stringify(data));
};

// Get data from sessionStorage
export const getSessionStorage = (key) => {
  try {
    const data = sessionStorage.getItem(key);
    // Only parse if data exists and isn't the string "undefined"
    if (data && data !== "undefined") {
      return JSON.parse(data);
    }
    return null;
  } catch (error) {
    console.error(`Error parsing session storage for key ${key}:`, error);
    return null;
  }
};

// Remove data from sessionStorage
export const removeSessionStorage = (key) => {
  sessionStorage.removeItem(key);
};

// Remove all data from sessionStorage
export const removeAllSessionStorage = () => {
  sessionStorage.clear();
};

export const isAuthenticated = () => {
  const token = Cookies.get("access_token");
  return !!token;
};

export const isEmpty = (obj) => {
  return Object.keys(obj).length === 0;
};

export const isEqual = (obj1, obj2) => {
  return JSON.stringify(obj1) === JSON.stringify(obj2);
};

/**
 * Converts an array of certificate bundle objects to CSV format and triggers download
 * @param {Array} certificates - Array of certificate bundle objects (GranularCertificateBundleReadFull)
 * @param {string} filename - Name of the CSV file to download
 */
export const downloadCertificatesAsCSV = (certificates, filename = "certificate_bundles_export.csv") => {
  // Define headers based on GranularCertificateBundleReadFull schema
  const headers = [

    "ID",
  
    // Mutable Attributes
    "Certificate Bundle Status",
    "Account ID", 
    "Certificate Bundle ID Range Start",
    "Certificate Bundle ID Range End",
    "Bundle Quantity (Wh)",
    
    // Bundle Characteristics
    "Issuance ID",
    "Energy Carrier",
    "Energy Source", 
    "Face Value (Wh)",
    "Issuance Post Energy Carrier Conversion",
    "Registry Configuration",
    "Hash",
    
    // Production Device Characteristics
    "Device ID",
    "Device Name",
    "Device Technology Type",
    "Device Production Start Date",
    "Device Power (MW)",
    "Device Energy (MWh)",
    "Device Location",
    
    // Temporal Characteristics
    "Production Starting Interval",
    "Production Ending Interval", 
    "Expiry Datestamp",
    
    // Storage Characteristics
    "Is Storage",
    "Allocated Storage Record ID",
    "Discharging Start Datetime",
    "Discharging End Datetime",
    "Storage Efficiency Factor",
    
    // Issuing Body Characteristics
    "Country of Issuance",
    "Connected Grid Identification",
    "Issuing Body",
    "Legal Status",
    "Issuance Purpose",
    "Support Received",
    "Quality Scheme Reference",
    "Dissemination Level",
    "Issue Market Zone",
    
    // Other Optional Characteristics
    "Emissions Factor Production Device",
    "Emissions Factor Source",
  ];
  
  if (!certificates || certificates.length === 0) {
    // Create empty CSV with headers
    const csvContent = headers.join(",") + "\n";
    downloadCSVFile(csvContent, filename);
    return;
  }

  // Convert certificate data to CSV rows
  const csvRows = certificates.map(cert => {
    return [

      cert.id || "",

      // Mutable Attributes
      cert.certificate_bundle_status || "",
      cert.account_id || "",
      cert.certificate_bundle_id_range_start || "0",
      cert.certificate_bundle_id_range_end || "",
      cert.bundle_quantity || "",
      
      // Bundle Characteristics
      cert.issuance_id || "",
      cert.energy_carrier || "",
      cert.energy_source || "",
      cert.face_value || "",
      cert.issuance_post_energy_carrier_conversion || "",
      cert.registry_configuration || "",
      cert.hash || "",
      
      // Production Device Characteristics
      cert.device_id || "",
      cert.device_name || "",
      cert.device_technology_type || "",
      cert.device_production_start_date || "",
      cert.device_power_mw || "",
      cert.device_energy_mwh || "",
      cert.device_location || "",
      
      // Temporal Characteristics
      cert.production_starting_interval || "",
      cert.production_ending_interval || "",
      cert.expiry_datestamp || "",
      
      // Storage Characteristics
      cert.is_storage || "",
      cert.allocated_storage_record_id || "",
      cert.discharging_start_datetime || "",
      cert.discharging_end_datetime || "",
      cert.storage_efficiency_factor || "",
      
      // Issuing Body Characteristics
      cert.country_of_issuance || "",
      cert.connected_grid_identification || "",
      cert.issuing_body || "",
      cert.legal_status || "",
      cert.issuance_purpose || "",
      cert.support_received || "",
      cert.quality_scheme_reference || "",
      cert.dissemination_level || "",
      cert.issue_market_zone || "",
      
      // Other Optional Characteristics
      cert.emissions_factor_production_device || "",
      cert.emissions_factor_source || "",

    ].map(field => `"${String(field).replace(/"/g, '""')}"`); // Escape quotes and wrap in quotes
  });

  const csvContent = [headers.join(","), ...csvRows.map(row => row.join(","))].join("\n");
  
  downloadCSVFile(csvContent, filename);
};

/**
 * Helper function to download CSV content as a file
 * @param {string} csvContent - The CSV content as a string
 * @param {string} filename - Name of the file to download
 */
const downloadCSVFile = (csvContent, filename) => {
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};