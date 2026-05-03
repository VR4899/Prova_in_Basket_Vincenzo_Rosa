const LOCAL_HOSTS = ["localhost", "127.0.0.1"];

export const publicSupportEmail =
  process.env.REACT_APP_PUBLIC_SUPPORT_EMAIL || "supporto@fiscofacile.it";

export const enableTestFeatures =
  process.env.REACT_APP_ENABLE_TEST_FEATURES === "true";

export const isLocalBrowser =
  typeof window !== "undefined" && LOCAL_HOSTS.includes(window.location.hostname);

export const showLocalTestFeatures = enableTestFeatures && isLocalBrowser;
