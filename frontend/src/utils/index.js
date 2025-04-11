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
