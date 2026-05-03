const TOKEN_KEY = "ff_admin_token";
const EXPIRES_KEY = "ff_admin_expires";

function hasWindow() {
  return typeof window !== "undefined";
}

function readValue(key) {
  if (!hasWindow()) return "";
  return window.sessionStorage.getItem(key) || window.localStorage.getItem(key) || "";
}

export function clearAdminSession() {
  if (!hasWindow()) return;
  window.sessionStorage.removeItem(TOKEN_KEY);
  window.sessionStorage.removeItem(EXPIRES_KEY);
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(EXPIRES_KEY);
}

export function getAdminToken() {
  return readValue(TOKEN_KEY);
}

export function getAdminExpiresAt() {
  return readValue(EXPIRES_KEY);
}

export function isAdminSessionExpired() {
  const expiresAt = getAdminExpiresAt();
  if (!expiresAt) return false;
  const timestamp = Date.parse(expiresAt);
  if (!Number.isFinite(timestamp)) return true;
  return timestamp <= Date.now();
}

export function hydrateAdminSession() {
  if (!hasWindow()) return;

  const token = window.localStorage.getItem(TOKEN_KEY);
  const expiresAt = window.localStorage.getItem(EXPIRES_KEY);
  if (!token || !expiresAt) return;

  const timestamp = Date.parse(expiresAt);
  if (!Number.isFinite(timestamp) || timestamp <= Date.now()) {
    clearAdminSession();
    return;
  }

  window.sessionStorage.setItem(TOKEN_KEY, token);
  window.sessionStorage.setItem(EXPIRES_KEY, expiresAt);
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(EXPIRES_KEY);
}

export function persistAdminSession(token, expiresAt) {
  if (!hasWindow()) return;
  clearAdminSession();
  window.sessionStorage.setItem(TOKEN_KEY, token);
  window.sessionStorage.setItem(EXPIRES_KEY, expiresAt);
}
