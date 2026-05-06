import { apiPaths, apiRequest } from './client';

export const api = {
  me: () => apiRequest(apiPaths.me),
  searchUsers: (query) => apiRequest(apiPaths.userSearch(query)),
  getUser: (userId) => apiRequest(apiPaths.userDetail(userId)),
  getUserDescriptionMe: () => apiRequest(apiPaths.userDescriptionMe),
  updateUserDescriptionMe: (data) =>
    apiRequest(apiPaths.userDescriptionMe, { method: 'PATCH', body: data }),
  getUserDescriptionForUser: (userId) => apiRequest(apiPaths.userDescriptionForUser(userId)),
  listProjects: () => apiRequest(apiPaths.projects),
  listGithubRepositories: () => apiRequest(apiPaths.projectGithubRepositories),
  importProjectFromGithub: (data) =>
    apiRequest(apiPaths.projectImport, { method: 'POST', body: data }),
  getProject: (projectId) => apiRequest(apiPaths.projectDetail(projectId)),
  updateProject: (projectId, data) =>
    apiRequest(apiPaths.projectDetail(projectId), { method: 'PATCH', body: data }),
  listProjectMembers: (projectId) => apiRequest(apiPaths.projectMembers(projectId)),
  inviteProjectMember: (projectId, data) =>
    apiRequest(apiPaths.projectMembers(projectId), { method: 'POST', body: data }),
  updateProjectMember: (projectId, memberId, data) =>
    apiRequest(apiPaths.projectMemberDetail(projectId, memberId), {
      method: 'PATCH',
      body: data,
    }),
  removeProjectMember: (projectId, memberId) =>
    apiRequest(apiPaths.projectMemberDetail(projectId, memberId), { method: 'DELETE' }),
  listProjectTasks: (projectId) => apiRequest(apiPaths.projectTasks(projectId)),
  getProjectTask: (projectId, taskId) => apiRequest(apiPaths.projectTaskDetail(projectId, taskId)),
  updateProjectTask: (projectId, taskId, data) =>
    apiRequest(apiPaths.projectTaskDetail(projectId, taskId), { method: 'PATCH', body: data }),
  deleteProjectTask: (projectId, taskId) =>
    apiRequest(apiPaths.projectTaskDetail(projectId, taskId), { method: 'DELETE' }),
  listProjectVulnerabilities: (projectId) => apiRequest(apiPaths.projectVulnerabilities(projectId)),
  getProjectVulnerability: (projectId, vulnerabilityId) =>
    apiRequest(apiPaths.projectVulnerabilityDetail(projectId, vulnerabilityId)),
  deleteProjectVulnerability: (projectId, vulnerabilityId) =>
    apiRequest(apiPaths.projectVulnerabilityDetail(projectId, vulnerabilityId), { method: 'DELETE' }),
  listProjectAuditLogs: (projectId) => apiRequest(apiPaths.projectAuditLogs(projectId)),
  getMeetingSettings: (projectId) => apiRequest(apiPaths.projectMeetingSettings(projectId)),
  updateMeetingSettings: (projectId, data, method = 'PATCH') =>
    apiRequest(apiPaths.projectMeetingSettings(projectId), { method, body: data }),
  listProjectBranches: (projectId) => apiRequest(apiPaths.projectBranches(projectId)),
  listSeniorSessions: () => apiRequest(apiPaths.srDevSessions),
  createSeniorSession: (data) =>
    apiRequest(apiPaths.srDevSessions, { method: 'POST', body: data }),
  getSeniorSession: (sessionId) => apiRequest(apiPaths.srDevSession(sessionId)),
  updateSeniorSession: (sessionId, data) =>
    apiRequest(apiPaths.srDevSession(sessionId), { method: 'PATCH', body: data }),
  listSeniorMessages: (sessionId) => apiRequest(apiPaths.srDevMessages(sessionId)),
  sendSeniorMessage: (sessionId, data, isForm = false) =>
    apiRequest(apiPaths.srDevMessages(sessionId), { method: 'POST', body: data, isForm }),
  listSeniorFindings: (sessionId) => apiRequest(apiPaths.srDevFindings(sessionId)),
  updateSeniorFindingStatus: (sessionId, findingId, status) =>
    apiRequest(apiPaths.srDevFinding(sessionId, findingId), {
      method: 'PATCH',
      body: { status },
    }),
  refreshToken: (refresh) =>
    apiRequest(apiPaths.authRefresh, { method: 'POST', body: { refresh } }),
  verifyToken: (token) => apiRequest(apiPaths.authVerify, { method: 'POST', body: { token } }),
};
