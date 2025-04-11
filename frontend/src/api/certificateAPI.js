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
