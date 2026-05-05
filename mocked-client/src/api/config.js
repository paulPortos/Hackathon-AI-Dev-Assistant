export const API_BASE_URL = 'http://localhost:8000';
export const API_VERSION = 'v1';
export const API_ROOT = `${API_BASE_URL}/api/${API_VERSION}`;

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
  }
};

export const getAbsoluteUrl = (path) => `${API_BASE_URL}${path}`;
