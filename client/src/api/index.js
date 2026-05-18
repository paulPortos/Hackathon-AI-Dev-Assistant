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

  // Kanban
  listBoards: () => apiRequest(apiPaths.boards),
  createBoard: (data) => apiRequest(apiPaths.boards, { method: 'POST', body: data }),
  getBoard: (id) => apiRequest(apiPaths.boardDetail(id)),
  updateBoard: (id, data) => apiRequest(apiPaths.boardDetail(id), { method: 'PATCH', body: data }),
  deleteBoard: (id) => apiRequest(apiPaths.boardDetail(id), { method: 'DELETE' }),

  listColumns: (boardId) => apiRequest(apiPaths.boardColumns(boardId)),
  createColumn: (boardId, data) =>
    apiRequest(apiPaths.boardColumns(boardId), { method: 'POST', body: data }),
  updateColumn: (id, data) => apiRequest(apiPaths.columnDetail(id), { method: 'PATCH', body: data }),
  deleteColumn: (id) => apiRequest(apiPaths.columnDetail(id), { method: 'DELETE' }),
  reorderColumn: (id, position) =>
    apiRequest(apiPaths.columnReorder(id), { method: 'PATCH', body: { position } }),

  listCards: (columnId, params = {}) => {
    let path = apiPaths.columnCards(columnId);
    const query = new URLSearchParams(params).toString();
    if (query) path += `?${query}`;
    return apiRequest(path);
  },
  createCard: (columnId, data) =>
    apiRequest(apiPaths.columnCards(columnId), { method: 'POST', body: data }),
  getCard: (id) => apiRequest(apiPaths.cardDetail(id)),
  updateCard: (id, data) => apiRequest(apiPaths.cardDetail(id), { method: 'PATCH', body: data }),
  deleteCard: (id) => apiRequest(apiPaths.cardDetail(id), { method: 'DELETE' }),
  moveCard: (id, data) => apiRequest(apiPaths.cardMove(id), { method: 'PATCH', body: data }),

  listBoardLabels: (boardId) => apiRequest(apiPaths.boardLabels(boardId)),
  createBoardLabel: (boardId, data) =>
    apiRequest(apiPaths.boardLabels(boardId), { method: 'POST', body: data }),
  attachCardLabel: (cardId, labelId) =>
    apiRequest(apiPaths.cardLabels(cardId), { method: 'POST', body: { label_id: labelId } }),
  detachCardLabel: (cardId, labelId) =>
    apiRequest(apiPaths.cardLabels(cardId), { method: 'DELETE', body: { label_id: labelId } }),

  listCardComments: (cardId) => apiRequest(apiPaths.cardComments(cardId)),
  createCardComment: (cardId, data) =>
    apiRequest(apiPaths.cardComments(cardId), { method: 'POST', body: data }),
  updateComment: (id, data) => apiRequest(apiPaths.commentDetail(id), { method: 'PATCH', body: data }),
  deleteComment: (id) => apiRequest(apiPaths.commentDetail(id), { method: 'DELETE' }),
  
  // Calendar
  getCalendar: (params = {}) => {
    let path = apiPaths.calendar;
    const query = new URLSearchParams(params).toString();
    if (query) path += `?${query}`;
    return apiRequest(path);
  },
  
  createEvent: (data) => apiRequest(apiPaths.calendarEvents, { method: 'POST', body: data }),
  listEvents: () => apiRequest(apiPaths.calendarEvents),
  updateEvent: (id, data) => apiRequest(`${apiPaths.calendarEvents}${id}/`, { method: 'PATCH', body: data }),
  deleteEvent: (id) => apiRequest(`${apiPaths.calendarEvents}${id}/`, { method: 'DELETE' }),

  // Scrum Sessions
  listScrumSessions: (projectId) => {
    let path = apiPaths.scrumSessions;
    if (projectId) path += `?project_id=${projectId}`;
    return apiRequest(path);
  },
  createScrumSession: (data) => apiRequest(apiPaths.scrumSessions, { method: 'POST', body: data }),
  getScrumSession: (sessionId) => apiRequest(apiPaths.scrumSessionDetail(sessionId)),
  listScrumMessages: (sessionId) => apiRequest(apiPaths.scrumSessionMessages(sessionId)),
  
  // GitHub Issues
  listGitHubIssues: (projectId, state = 'open') => 
    apiRequest(`${apiPaths.projectGitHubIssues(projectId)}?state=${state}`),
  syncGitHubIssues: (projectId) => 
    apiRequest(apiPaths.projectGitHubIssuesSync(projectId), { method: 'POST' }),
  deleteScrumSession: (sessionId) =>
    apiRequest(apiPaths.scrumSessionDetail(sessionId), { method: 'DELETE' }),
};
