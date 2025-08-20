import baseAPI from "./baseAPI";

export const fetchCertificatesAPI = (_) => {
  return baseAPI.post("/certificate/query", _);
};

export const createCertificateAPI = (certificateData) =>
  baseAPI.post("/certificate", certificateData);

export const transferCertificateAPI = (certificateData) =>
  baseAPI.post("/certificate/transfer", certificateData);

export const cancelCertificateAPI = (certificateData) =>
  baseAPI.post("/certificate/cancel", certificateData);

export const getCertificateDetailsAPI = (certificateId) => {
  return baseAPI.get(`/certificate/${certificateId}`);
};

export const downloadCertificateImportTemplateAPI = () => {
  return baseAPI.get("/certificate/certificate_import_template", {
    responseType: "blob",
  });
};

export const importCertificatesAPI = (formData) => {
  return baseAPI.post("/certificate/import", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
};

export const downloadCertificatesAPI = (queryData) => {
  return baseAPI.post("/certificate/query_full", queryData);
};

export const downloadSelectedCertificateAPI = (certificateId) => {
  return baseAPI.get(`/certificate/${certificateId}`);
};