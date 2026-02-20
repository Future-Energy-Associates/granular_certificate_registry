import baseAPI from "./baseAPI";

export const getStorageRecordsAPI = (deviceId) => {
  return baseAPI.get(`/storage/storage_records/${deviceId}`);
};

export const getAllocatedStorageRecordsAPI = (deviceId) => {
  return baseAPI.get(`/storage/allocated_storage_records/${deviceId}`);
};

// Get storage records for all devices in the account
export const getAllStorageRecordsForAccountAPI = async (deviceIds) => {
  const promises = deviceIds.map(deviceId =>
    getStorageRecordsAPI(deviceId).catch(error => {
      // Return empty array if device has no storage records or any error occurs
      if (error?.response?.status === 404) {
        return { data: [] };
      }
      // For any other error, also return empty array instead of throwing
      return { data: [] };
    })
  );

  const results = await Promise.all(promises);
  return results.flatMap(result => result.data || []);
};

// Get allocated storage records for all devices in the account
export const getAllAllocatedStorageRecordsForAccountAPI = async (deviceIds) => {
  const promises = deviceIds.map(deviceId =>
    getAllocatedStorageRecordsAPI(deviceId).catch(error => {
      // Return empty array if device has no allocated storage records or any error occurs
      if (error?.response?.status === 404) {
        return { data: [] };
      }
      // For any other error, also return empty array instead of throwing
      return { data: [] };
    })
  );

  const results = await Promise.all(promises);
  return results.flatMap(result => result.data || []);
};
