const TOKEN_KEY = "ff_customer_token";
const EXPIRES_KEY = "ff_customer_expires";

function hasWindow() {
  return typeof window !== "undefined";
}

export function clearCustomerSession() {
  if (!hasWindow()) return;
  window.sessionStorage.removeItem(TOKEN_KEY);
  window.sessionStorage.removeItem(EXPIRES_KEY);
}

export function getCustomerToken() {
  if (!hasWindow()) return "";
  return window.sessionStorage.getItem(TOKEN_KEY) || "";
}

export function getCustomerExpiresAt() {
  if (!hasWindow()) return "";
  return window.sessionStorage.getItem(EXPIRES_KEY) || "";
}

export function isCustomerSessionExpired() {
  const expiresAt = getCustomerExpiresAt();
  if (!expiresAt) return false;
  const timestamp = Date.parse(expiresAt);
  if (!Number.isFinite(timestamp)) return true;
  return timestamp <= Date.now();
}

export function persistCustomerSession(token, expiresAt) {
  if (!hasWindow()) return;
  clearCustomerSession();
  window.sessionStorage.setItem(TOKEN_KEY, token);
  window.sessionStorage.setItem(EXPIRES_KEY, expiresAt);
}
