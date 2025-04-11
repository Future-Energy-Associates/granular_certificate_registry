import baseAPI from "./baseAPI";

export const createDeviceAPI = (deviceData) => {
  return baseAPI.post("/device/create", deviceData);
};

export const submitMeterReadingsAPI = (formData) => {
  return baseAPI.post("/measurement/submit_readings", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
};

export const downloadMeterReadingsTemplateAPI = () => {
  return baseAPI.get("/measurement/meter_readings_template", {
    responseType: "blob",
  });
};
