import baseAPI from "./baseAPI";

export const readUserAPI = (userID) => {
  return baseAPI.get(`/user/${userID}`);
};

export const readCurrentUserAPI = () => {
  return baseAPI.get(`/user/me`);
};
