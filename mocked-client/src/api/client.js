import { API_BASE_URL, API_VERSION, ENDPOINTS, API_ROOT } from './config';

const ACCESS_TOKEN_KEY = 'mocked-client.access-token';
const REFRESH_TOKEN_KEY = 'mocked-client.refresh-token';

const getAccessToken = () => localStorage.getItem(ACCESS_TOKEN_KEY) || '';
const getRefreshToken = () => localStorage.getItem(REFRESH_TOKEN_KEY) || '';

const setTokens = ({ access, refresh }) => {
  if (access) {
    localStorage.setItem(ACCESS_TOKEN_KEY, access);
  }
  if (refresh) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
  }
};

const clearTokens = () => {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
};

export const authStorage = {
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,
};

export const authUrls = {
  login: `${API_BASE_URL}${ENDPOINTS.AUTH.GITHUB_LOGIN}`,
  callback: `${API_BASE_URL}${ENDPOINTS.AUTH.GITHUB_CALLBACK}`,
};

export const apiPaths = {
  me: ENDPOINTS.USERS.ME,
  userSearch: (query) => `/users/search/?q=${encodeURIComponent(query || '')}`,
  userDetail: (userId) => `/users/${userId}/`,
  userDescriptionMe: '/user-descriptions/current-user/',
  userDescriptionForUser: (userId) => `/user-descriptions/users/${userId}/`,
  projects: ENDPOINTS.PROJECTS.LIST,
  projectImport: ENDPOINTS.PROJECTS.IMPORT,
  projectGithubRepositories: ENDPOINTS.PROJECTS.GITHUB_REPOS,
  projectDetail: ENDPOINTS.PROJECTS.DETAIL,
  projectMembers: (projectId) => `/projects/${projectId}/members/`,
  projectMemberDetail: (projectId, memberId) => `/projects/${projectId}/members/${memberId}/`,
  projectTasks: ENDPOINTS.PROJECTS.TASKS,
  projectVulnerabilities: ENDPOINTS.PROJECTS.VULNERABILITIES,
  projectMeetingSettings: (projectId) => `/projects/${projectId}/meeting-settings/`,
  projectBranches: (projectId) => `/projects/${projectId}/repository/branches/`,
  srDevSessions: '/agents/sr-dev/sessions/',
  srDevSession: (sessionId) => `/agents/sr-dev/sessions/${sessionId}/`,
  srDevMessages: (sessionId) => `/agents/sr-dev/sessions/${sessionId}/messages/`,
  authRefresh: '/auth/tokens/refresh/',
  authVerify: '/auth/tokens/verify/',
};

const buildApiUrl = (path) => {
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  return `${API_ROOT}${path}`;
};

const safeJsonParse = (text) => {
  try {
    return { ok: true, value: JSON.parse(text) };
  } catch (error) {
    return { ok: false, value: null, error };
  }
};

const parseResponse = async (response) => {
  const text = await response.text();
  if (!text) {
    return null;
  }
  const parsed = safeJsonParse(text);
  return parsed.ok ? parsed.value : text;
};

const resolveErrorMessage = (payload, response) => {
  if (payload && typeof payload === 'object') {
    if (payload.detail) {
      return payload.detail;
    }
    if (payload.message) {
      return payload.message;
    }
  }
  if (typeof payload === 'string' && payload.trim()) {
    return payload;
  }
  return `Request failed with status ${response.status}`;
};

export const normalizeList = (payload) => {
  if (Array.isArray(payload)) {
    return payload;
  }
  if (payload && Array.isArray(payload.results)) {
    return payload.results;
  }
  return [];
};

export async function apiRequest(path, options = {}) {
  const {
    method = 'GET',
    body,
    headers = {},
    auth = true,
    isForm = false,
  } = options;

  const requestHeaders = { ...headers };
  if (auth) {
    const token = getAccessToken();
    if (token) {
      requestHeaders.Authorization = `Bearer ${token}`;
    }
  }

  let requestBody;
  if (body !== undefined) {
    if (isForm) {
      requestBody = body;
    } else {
      requestHeaders['Content-Type'] = 'application/json';
      requestBody = JSON.stringify(body);
    }
  }

  const response = await fetch(buildApiUrl(path), {
    method,
    headers: requestHeaders,
    body: requestBody,
  });

  const payload = await parseResponse(response);
  if (!response.ok) {
    throw new Error(resolveErrorMessage(payload, response));
  }

  return payload;
}

export const apiConfig = {
  API_BASE_URL,
  API_VERSION,
  API_ROOT,
};
