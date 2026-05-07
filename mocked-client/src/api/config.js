const trimTrailingSlash = (value) => String(value || '').replace(/\/+$/, '');
const trimSlashes = (value) => String(value || '').replace(/^\/+|\/+$/g, '');

export const API_BASE_URL = trimTrailingSlash(
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
);
export const API_VERSION = trimSlashes(import.meta.env.VITE_API_VERSION || 'v1');
export const API_ROOT = `${API_BASE_URL}/api/${API_VERSION}`;

const resolveWsBaseUrl = (baseUrl) => {
  if (baseUrl.startsWith('https://')) {
    return baseUrl.replace('https://', 'wss://');
  }
  if (baseUrl.startsWith('http://')) {
    return baseUrl.replace('http://', 'ws://');
  }
  return baseUrl;
};

export const WS_BASE_URL = trimTrailingSlash(
  import.meta.env.VITE_WS_BASE_URL || resolveWsBaseUrl(API_BASE_URL),
);
export const WS_ROOT = `${WS_BASE_URL}/ws`;

export const ENDPOINTS = {
  AUTH: {
    GITHUB_LOGIN: `/auth/github/login/`,
    GITHUB_CALLBACK: `/auth/github/callback/`,
  },
  PROJECTS: {
    LIST: `/projects/`,
    GITHUB_REPOS: `/projects/github/repositories/`,
    IMPORT: `/projects/import-from-github/`,
    DETAIL: (id) => `/projects/${id}/`,
    TASKS: (id) => `/projects/${id}/tasks/`,
    VULNERABILITIES: (id) => `/projects/${id}/vulnerabilities/`,
  },
  USERS: {
    ME: `/users/me/`,
  },
  KANBAN: {
    BOARDS: `/boards/`,
    BOARD_DETAIL: (id) => `/boards/${id}/`,
    BOARD_COLUMNS: (id) => `/boards/${id}/columns/`,
    COLUMN_DETAIL: (id) => `/columns/${id}/`,
    COLUMN_REORDER: (id) => `/columns/${id}/reorder/`,
    COLUMN_CARDS: (id) => `/columns/${id}/cards/`,
    CARD_DETAIL: (id) => `/cards/${id}/`,
    CARD_MOVE: (id) => `/cards/${id}/move/`,
    BOARD_LABELS: (id) => `/boards/${id}/labels/`,
    CARD_LABELS: (id) => `/cards/${id}/labels/`,
    CARD_COMMENTS: (id) => `/cards/${id}/comments/`,
    COMMENT_DETAIL: (id) => `/comments/${id}/`,
  },
  CALENDAR: '/calendar/',
  CALENDAR_EVENTS: '/calendar/events/',
};

export const getAbsoluteUrl = (path) => `${API_BASE_URL}${path}`;
