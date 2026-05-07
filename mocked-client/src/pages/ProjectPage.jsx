import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { api } from '../api';
import { normalizeList } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import Modal from '../components/Modal';
import SectionCard from '../components/SectionCard';
import { GitHubIcon } from '../components/Icons';

const TASK_CATEGORY_OPTIONS = [
  ['vulnerability_fix', 'Vulnerability fix'],
  ['feature', 'Feature'],
  ['bug', 'Bug'],
  ['refactor', 'Refactor'],
  ['research', 'Research'],
  ['other', 'Other'],
];

const TASK_PRIORITY_OPTIONS = [
  ['critical', 'Critical'],
  ['high', 'High'],
  ['medium', 'Medium'],
  ['low', 'Low'],
];

const TASK_STATUS_OPTIONS = [
  ['todo', 'Todo'],
  ['in_progress', 'In progress'],
  ['blocked', 'Blocked'],
  ['completed', 'Completed'],
  ['canceled', 'Canceled'],
];

const WEEKDAY_OPTIONS = [
  ['monday', 'Monday'],
  ['tuesday', 'Tuesday'],
  ['wednesday', 'Wednesday'],
  ['thursday', 'Thursday'],
  ['friday', 'Friday'],
  ['saturday', 'Saturday'],
  ['sunday', 'Sunday'],
];

const TIMEZONE_OPTIONS = [
  ['Asia/Manila', 'Philippines - Asia/Manila'],
  ['Asia/Singapore', 'Singapore - Asia/Singapore'],
  ['Asia/Tokyo', 'Japan - Asia/Tokyo'],
  ['Australia/Sydney', 'Australia - Australia/Sydney'],
  ['Europe/London', 'UK - Europe/London'],
  ['America/Los_Angeles', 'US Pacific - America/Los_Angeles'],
  ['America/New_York', 'US Eastern - America/New_York'],
  ['UTC', 'UTC'],
];

const ALERT_OPTIONS = [
  [10, '10 minutes before'],
  [15, '15 minutes before'],
  [30, '30 minutes before'],
  [60, '1 hour before'],
  [1440, '1 day before'],
];

const DISPLAY_ROLE_OPTIONS = [
  'Owner',
  'Project Lead',
  'Frontend Developer',
  'Backend Developer',
  'Full-stack Developer',
  'Mobile Developer',
  'QA Engineer',
  'Security Reviewer',
  'Product/PM',
  'Designer',
  'Contributor',
];

const ROLE_TAG_OPTIONS = [
  'owner',
  'lead',
  'frontend',
  'backend',
  'mobile',
  'qa',
  'security',
  'product',
  'design',
  'docs',
];

const emptyContextDraft = {
  overview: '',
  goals: '',
  tech_stack: '',
  business_context: '',
  agent_notes: '',
};

const meetingDefaults = {
  meeting_days: ['monday', 'wednesday', 'friday'],
  meeting_time: '09:00:00',
  timezone: 'Asia/Manila',
  google_meet_link: '',
  weekly_goals: '',
  monthly_goals: '',
  alert_minutes_before: 30,
  is_active: true,
};

const toList = (value) =>
  String(value || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);

const toggleTextTag = (value, tag) => {
  const items = toList(value);
  if (items.includes(tag)) {
    return items.filter((item) => item !== tag).join(', ');
  }
  return [...items, tag].join(', ');
};

const selectValues = (event) =>
  Array.from(event.target.selectedOptions).map((option) => option.value);

const formatTimeLabel = (value) => {
  const [hourText, minute] = value.split(':');
  const hour = Number(hourText);
  const period = hour >= 12 ? 'PM' : 'AM';
  const hour12 = hour % 12 || 12;
  return `${hour12}:${minute} ${period}`;
};

const timeOptions = Array.from({ length: 29 }, (_, index) => {
  const totalMinutes = 8 * 60 + index * 30;
  const hour = Math.floor(totalMinutes / 60);
  const minute = totalMinutes % 60;
  return `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}:00`;
});

const isAssignedToUser = (task, user) =>
  Boolean(task?.assigned_to_user_id && user?.id && task.assigned_to_user_id === user.id);

export default function ProjectPage() {
  const { projectId } = useParams();
  const { user } = useAuth();
  const [project, setProject] = useState(null);
  const [members, setMembers] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [vulnerabilities, setVulnerabilities] = useState([]);
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState('');

  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchError, setSearchError] = useState('');

  const [inviteUserId, setInviteUserId] = useState('');
  const [inviteDisplayRole, setInviteDisplayRole] = useState('Contributor');
  const [inviteRolesText, setInviteRolesText] = useState('frontend');
  const [inviteNotice, setInviteNotice] = useState('');

  const [profileModalOpen, setProfileModalOpen] = useState(false);
  const [profileUser, setProfileUser] = useState(null);
  const [profileDescription, setProfileDescription] = useState(null);
  const [profileError, setProfileError] = useState('');

  const [contextModalOpen, setContextModalOpen] = useState(false);
  const [contextDraft, setContextDraft] = useState(emptyContextDraft);
  const [contextNotice, setContextNotice] = useState('');
  const [contextError, setContextError] = useState('');

  const [taskModalOpen, setTaskModalOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  const [taskDraft, setTaskDraft] = useState(null);
  const [taskError, setTaskError] = useState('');

  const [vulnerabilityError, setVulnerabilityError] = useState('');

  const [memberModalOpen, setMemberModalOpen] = useState(false);
  const [selectedMember, setSelectedMember] = useState(null);
  const [memberDraft, setMemberDraft] = useState(null);
  const [memberError, setMemberError] = useState('');

  const [inviteModalOpen, setInviteModalOpen] = useState(false);
  const [meetingModalOpen, setMeetingModalOpen] = useState(false);
  const [meetingDraft, setMeetingDraft] = useState(null);
  const [meetingNotice, setMeetingNotice] = useState('');
  const [meetingError, setMeetingError] = useState('');

  const isOwner = Boolean(project?.creator_id && user?.id && project.creator_id === user.id);

  const loadProject = async () => {
    setStatus('loading');
    setError('');
    try {
      const [projectPayload, taskPayload, vulnerabilityPayload, memberPayload] =
        await Promise.all([
          api.getProject(projectId),
          api.listProjectTasks(projectId),
          api.listProjectVulnerabilities(projectId),
          api.listProjectMembers(projectId),
        ]);
      setProject(projectPayload);
      setTasks(normalizeList(taskPayload));
      setVulnerabilities(normalizeList(vulnerabilityPayload));
      setMembers(normalizeList(memberPayload));
      setStatus('ready');
    } catch (err) {
      setStatus('error');
      setError(err.message);
    }
  };

  useEffect(() => {
    if (projectId) {
      loadProject();
    }
  }, [projectId]);

  const vulnerabilityOptions = useMemo(
    () => vulnerabilities.map((item) => [String(item.id), item.title]),
    [vulnerabilities],
  );

  const memberOptions = useMemo(
    () => members.map((member) => [String(member.id), member.name || member.username]),
    [members],
  );

  const handleSearch = async () => {
    setSearchError('');
    setInviteNotice('');
    if (!searchQuery.trim()) {
      setSearchResults([]);
      setSearchError('Enter a username or email to search.');
      return;
    }
    try {
      const payload = await api.searchUsers(searchQuery);
      setSearchResults(normalizeList(payload));
    } catch (err) {
      setSearchResults([]);
      setSearchError(err.message);
    }
  };

  const handleInvite = async () => {
    setInviteNotice('');
    setSearchError('');
    if (!inviteUserId) {
      setSearchError('Select a user to invite.');
      return;
    }
    try {
      const payload = await api.inviteProjectMember(projectId, {
        user_id: Number(inviteUserId),
        display_role: inviteDisplayRole,
        roles: toList(inviteRolesText),
      });
      setMembers((prev) => [...prev, payload]);
      setInviteUserId('');
      setInviteNotice('Member added.');
    } catch (err) {
      setSearchError(err.message);
    }
  };

  const openProfileModal = async (userId) => {
    setProfileModalOpen(true);
    setProfileUser(null);
    setProfileDescription(null);
    setProfileError('');
    try {
      const userPayload = await api.getUser(userId);
      setProfileUser(userPayload);
      try {
        const descriptionPayload = await api.getUserDescriptionForUser(userId);
        setProfileDescription(descriptionPayload);
      } catch {
        setProfileDescription(null);
      }
    } catch (err) {
      setProfileError(err.message);
    }
  };

  const openContextModal = () => {
    if (!project) return;
    setContextDraft({
      overview: project.overview || '',
      goals: project.goals || '',
      tech_stack: (project.tech_stack || []).join(', '),
      business_context: project.business_context || '',
      agent_notes: project.agent_notes || '',
    });
    setContextError('');
    setContextNotice('');
    setContextModalOpen(true);
  };

  const handleContextSave = async () => {
    setContextError('');
    setContextNotice('');
    try {
      const payload = await api.updateProject(projectId, {
        overview: contextDraft.overview,
        goals: contextDraft.goals,
        tech_stack: toList(contextDraft.tech_stack),
        business_context: contextDraft.business_context,
        agent_notes: contextDraft.agent_notes,
      });
      setProject(payload);
      setContextNotice('Project context saved.');
    } catch (err) {
      setContextError(err.message);
    }
  };

  const openTaskModal = (task) => {
    const canEdit = isOwner || isAssignedToUser(task, user);
    if (!canEdit) return;
    setSelectedTask(task);
    setTaskDraft({
      title: task.title || '',
      description: task.description || '',
      category: task.category || 'other',
      priority: task.priority || 'medium',
      status: task.status || 'todo',
      assigned_to_id: task.assigned_to_id ? String(task.assigned_to_id) : '',
      related_finding_id: task.related_finding_id ? String(task.related_finding_id) : '',
      due_date: task.due_date || '',
    });
    setTaskError('');
    setTaskModalOpen(true);
  };

  const handleTaskSave = async () => {
    if (!selectedTask || !taskDraft) return;
    setTaskError('');
    try {
      const payload = isOwner
        ? {
            title: taskDraft.title,
            description: taskDraft.description,
            category: taskDraft.category,
            priority: taskDraft.priority,
            status: taskDraft.status,
            assigned_to_id: taskDraft.assigned_to_id ? Number(taskDraft.assigned_to_id) : null,
            related_finding_id: taskDraft.related_finding_id
              ? Number(taskDraft.related_finding_id)
              : null,
            due_date: taskDraft.due_date || null,
          }
        : { status: taskDraft.status };
      const updatedTask = await api.updateProjectTask(projectId, selectedTask.id, payload);
      setTasks((prev) => prev.map((task) => (task.id === updatedTask.id ? updatedTask : task)));
      setTaskModalOpen(false);
      setSelectedTask(null);
      setTaskDraft(null);
    } catch (err) {
      setTaskError(err.message);
    }
  };

  const handleDeleteVulnerability = async (vulnerability) => {
    if (!isOwner) return;
    setVulnerabilityError('');
    const confirmed = window.confirm(
      `Delete vulnerability "${vulnerability.title}"? This permanently removes it from the project.`,
    );
    if (!confirmed) return;
    try {
      await api.deleteProjectVulnerability(projectId, vulnerability.id);
      setVulnerabilities((prev) => prev.filter((item) => item.id !== vulnerability.id));
    } catch (err) {
      setVulnerabilityError(err.message);
    }
  };

  const openMemberModal = (member) => {
    if (!isOwner) return;
    setSelectedMember(member);
    setMemberDraft({
      display_role: member.display_role || 'Contributor',
      roles: (member.roles || []).join(', '),
    });
    setMemberError('');
    setMemberModalOpen(true);
  };

  const handleMemberSave = async () => {
    if (!selectedMember || !memberDraft) return;
    setMemberError('');
    try {
      const payload = await api.updateProjectMember(projectId, selectedMember.id, {
        display_role: memberDraft.display_role,
        roles: toList(memberDraft.roles),
      });
      setMembers((prev) => prev.map((member) => (member.id === payload.id ? payload : member)));
      setMemberModalOpen(false);
      setSelectedMember(null);
      setMemberDraft(null);
    } catch (err) {
      setMemberError(err.message);
    }
  };

  const handleRemoveMember = async (member) => {
    if (!isOwner) return;
    setMemberError('');
    const confirmed = window.confirm(`Remove ${member.name || member.username} from this project?`);
    if (!confirmed) return;
    try {
      await api.removeProjectMember(projectId, member.id);
      setMembers((prev) => prev.filter((item) => item.id !== member.id));
      if (selectedMember?.id === member.id) {
        setMemberModalOpen(false);
        setSelectedMember(null);
        setMemberDraft(null);
      }
    } catch (err) {
      setMemberError(err.message);
    }
  };

  const openMeetingModal = async () => {
    setMeetingModalOpen(true);
    setMeetingError('');
    setMeetingNotice('');
    try {
      const settings = await api.getMeetingSettings(projectId);
      setMeetingDraft({
        meeting_days: Array.isArray(settings.meeting_days)
          ? settings.meeting_days
          : meetingDefaults.meeting_days,
        meeting_time: settings.meeting_time || meetingDefaults.meeting_time,
        timezone: settings.timezone || meetingDefaults.timezone,
        google_meet_link: settings.google_meet_link || '',
        weekly_goals: settings.weekly_goals || '',
        monthly_goals: settings.monthly_goals || '',
        alert_minutes_before: settings.alert_minutes_before || meetingDefaults.alert_minutes_before,
        is_active: settings.is_active,
      });
    } catch {
      setMeetingDraft(meetingDefaults);
      setMeetingError('No meeting settings yet. Review the PH defaults, add a Meet link, then save.');
    }
  };

  const handleMeetingSave = async () => {
    setMeetingError('');
    setMeetingNotice('');
    if (!meetingDraft?.google_meet_link?.trim()) {
      setMeetingError('Google Meet link is required before saving meeting settings.');
      return;
    }
    try {
      const payload = {
        meeting_days: meetingDraft.meeting_days,
        meeting_time: meetingDraft.meeting_time,
        timezone: meetingDraft.timezone,
        google_meet_link: meetingDraft.google_meet_link,
        weekly_goals: meetingDraft.weekly_goals,
        monthly_goals: meetingDraft.monthly_goals,
        alert_minutes_before: Number(meetingDraft.alert_minutes_before) || 30,
        is_active: Boolean(meetingDraft.is_active),
      };
      const savedSettings = await api.updateMeetingSettings(projectId, payload, 'PATCH');
      setMeetingDraft({
        ...savedSettings,
        meeting_days: savedSettings.meeting_days || meetingDefaults.meeting_days,
      });
      setMeetingNotice('Meeting settings saved.');
    } catch (err) {
      setMeetingError(err.message);
    }
  };

  return (
    <div className="grid">
      {status === 'error' ? <p className="subtle">{error}</p> : null}

      <section className="grid two" style={{ alignItems: 'stretch' }}>
        <SectionCard
          title="Project Workspace"
          actions={project ? (
            <>
              <Link className="button ghost compact" to="/projects">
                Back to projects
              </Link>
              <button
                className="button ghost compact"
                type="button"
                onClick={openMeetingModal}
                disabled={!isOwner}
                title={isOwner ? 'Update meeting settings' : 'Only the project creator can update meetings'}
              >
                Meeting settings
              </button>
              <Link className="button ghost compact" to="/kanban">
                Kanban board
              </Link>
              <Link className="button secondary compact" to={`/senior?projectId=${project.id}`}>
                Report to senior
              </Link>
            </>
          ) : null}
        >
          <p className="subtle" style={{ marginBottom: '16px' }}>
            Review vulnerabilities, update tasks, manage contributors, and keep
            project context ready for Visor.
          </p>

          {project && (
            <div style={{ marginBottom: '20px' }}>
              <h2 style={{ margin: '0 0 4px', fontSize: '18px' }}>{project.github_full_name}</h2>
              <div className="inline-actions" style={{ gap: '8px' }}>
                <span className="pill" style={{ background: 'var(--accent-100)', color: 'var(--accent-700)' }}>
                  {project.github_primary_language || 'No language'}
                </span>
                <span className="pill" style={{ background: 'rgba(0,0,0,0.05)' }}>
                  {project.github_visibility}
                </span>
                {project.github_html_url ? (
                  <a className="button ghost compact" href={project.github_html_url} target="_blank" rel="noreferrer">
                    <GitHubIcon size={14} />
                    GitHub
                  </a>
                ) : null}
              </div>
            </div>
          )}
        </SectionCard>

        <SectionCard
          title="Project Context"
          actions={
            isOwner ? (
              <button className="button ghost compact" type="button" onClick={openContextModal}>
                Edit context
              </button>
            ) : null
          }
        >
          <div className="detail-stack">
            <div>
              <p className="meta-label">Overview</p>
              <p>{project?.overview || 'No overview defined yet.'}</p>
            </div>
            <div>
              <p className="meta-label">Goals</p>
              <p>{project?.goals || 'No goals defined yet.'}</p>
            </div>
            <div>
              <p className="meta-label">Tech Stack</p>
              <div className="tag-row">
                {(project?.tech_stack || []).map((item) => (
                  <span key={item} className="tag">{item}</span>
                ))}
                {(project?.tech_stack || []).length === 0 ? <span className="subtle">---</span> : null}
              </div>
            </div>
            <div>
              <p className="meta-label">Business Context</p>
              <p>{project?.business_context || '---'}</p>
            </div>
            <div>
              <p className="meta-label">Agent Notes</p>
              <p>{project?.agent_notes || '---'}</p>
            </div>
          </div>
        </SectionCard>
      </section>

      <section className="grid two">
        <SectionCard title="Vulnerabilities">
          {vulnerabilityError ? <p className="subtle">{vulnerabilityError}</p> : null}
          <div className="scroll-area">
            <ul className="list">
              {vulnerabilities.map((vulnerability) => (
                <li key={vulnerability.id}>
                  <div className="item-header">
                    <strong>{vulnerability.title}</strong>
                    {isOwner ? (
                      <button
                        className="button ghost compact danger"
                        type="button"
                        onClick={() => handleDeleteVulnerability(vulnerability)}
                      >
                        Delete
                      </button>
                    ) : null}
                  </div>
                  <p className="subtle">{vulnerability.summary || vulnerability.recommendation}</p>
                  <div className="tag-row">
                    <span className="tag">{vulnerability.severity}</span>
                    <span className="tag">{vulnerability.status}</span>
                    {vulnerability.affected_path ? <span className="tag">{vulnerability.affected_path}</span> : null}
                  </div>
                </li>
              ))}
              {vulnerabilities.length === 0 && <p className="subtle">No vulnerabilities reported.</p>}
            </ul>
          </div>
        </SectionCard>

        <SectionCard title="Tasks">
          <div className="scroll-area">
            <ul className="list">
              {tasks.map((task) => {
                const canEditTask = isOwner || isAssignedToUser(task, user);
                return (
                  <li key={task.id}>
                    <div className="item-header">
                      <strong>{task.title}</strong>
                      {canEditTask ? (
                        <button
                          className="button ghost compact"
                          type="button"
                          onClick={() => openTaskModal(task)}
                        >
                          Edit
                        </button>
                      ) : null}
                    </div>
                    <p className="subtle">{task.description || task.reasoning || 'No description.'}</p>
                    <div className="tag-row">
                      <span className="tag">{task.priority}</span>
                      <span className="tag">{task.status}</span>
                      {task.assigned_to_username ? <span className="tag">@{task.assigned_to_username}</span> : null}
                    </div>
                  </li>
                );
              })}
              {tasks.length === 0 && <p className="subtle">No tasks assigned.</p>}
            </ul>
          </div>
        </SectionCard>
      </section>

      <section className="grid">
        <SectionCard
          title="Members"
          actions={
            isOwner ? (
              <button className="button" type="button" onClick={() => setInviteModalOpen(true)}>
                Invite Member
              </button>
            ) : null
          }
        >
          {memberError ? <p className="subtle">{memberError}</p> : null}
          <div className="member-grid">
            {members.map((member) => (
              <article key={member.id} className="member-card">
                <div className="member-card-header">
                  <div className="avatar small">{member.username?.[0]?.toUpperCase() || 'U'}</div>
                  <div>
                    <strong>{member.name || member.username}</strong>
                    <p className="subtle">@{member.username}</p>
                  </div>
                </div>
                <div className="tag-row">
                  <span className="tag">{member.display_role}</span>
                  {(member.roles || []).map((role) => (
                    <span key={role} className="tag">{role}</span>
                  ))}
                </div>
                <div className="inline-actions">
                  <button
                    className="button ghost compact"
                    type="button"
                    onClick={() => openProfileModal(member.user_id)}
                  >
                    View profile
                  </button>
                  {isOwner ? (
                    <>
                      <button
                        className="button ghost compact"
                        type="button"
                        onClick={() => openMemberModal(member)}
                      >
                        Manage
                      </button>
                      <button
                        className="button ghost compact danger"
                        type="button"
                        onClick={() => handleRemoveMember(member)}
                      >
                        Remove
                      </button>
                    </>
                  ) : null}
                </div>
              </article>
            ))}
            {members.length === 0 && <p className="subtle">No members in this project yet.</p>}
          </div>
        </SectionCard>
      </section>

      <Modal
        isOpen={profileModalOpen}
        title="User profile"
        onClose={() => setProfileModalOpen(false)}
      >
        {profileError ? <p className="subtle">{profileError}</p> : null}
        {profileUser ? (
          <div className="grid">
            <div className="profile-row">
              <div className="avatar">{profileUser.username?.[0]?.toUpperCase() || 'U'}</div>
              <div>
                <strong>{profileUser.name || profileUser.username}</strong>
                <p className="subtle">@{profileUser.username}</p>
                <p className="subtle">{profileUser.email || 'No public email'}</p>
              </div>
            </div>
            {profileDescription ? (
              <div className="detail-stack">
                <p className="subtle">{profileDescription.summary || 'No profile summary yet.'}</p>
                <p className="subtle">
                  Role: {profileDescription.primary_role} ({profileDescription.experience_level})
                </p>
                <div className="tag-row">
                  {(profileDescription.skills || []).map((skill) => (
                    <span key={skill.name} className="tag">{skill.name} {skill.level}/5</span>
                  ))}
                </div>
              </div>
            ) : (
              <p className="subtle">No user description yet.</p>
            )}
          </div>
        ) : (
          <p className="subtle">Loading user profile...</p>
        )}
      </Modal>

      <Modal
        isOpen={contextModalOpen}
        title="Edit Project Context"
        onClose={() => setContextModalOpen(false)}
      >
        <div className="grid">
          <div className="field">
            <label className="label" htmlFor="project-overview">Overview</label>
            <textarea
              id="project-overview"
              className="textarea"
              value={contextDraft.overview}
              onChange={(event) => setContextDraft((prev) => ({ ...prev, overview: event.target.value }))}
            />
          </div>
          <div className="field">
            <label className="label" htmlFor="project-goals">Goals</label>
            <textarea
              id="project-goals"
              className="textarea"
              value={contextDraft.goals}
              onChange={(event) => setContextDraft((prev) => ({ ...prev, goals: event.target.value }))}
            />
          </div>
          <div className="field">
            <label className="label" htmlFor="project-tech-stack">Tech stack</label>
            <input
              id="project-tech-stack"
              className="input"
              value={contextDraft.tech_stack}
              onChange={(event) => setContextDraft((prev) => ({ ...prev, tech_stack: event.target.value }))}
              placeholder="Django, React, PostgreSQL"
            />
          </div>
          <div className="field">
            <label className="label" htmlFor="project-business-context">Business context</label>
            <textarea
              id="project-business-context"
              className="textarea"
              value={contextDraft.business_context}
              onChange={(event) => setContextDraft((prev) => ({ ...prev, business_context: event.target.value }))}
            />
          </div>
          <div className="field">
            <label className="label" htmlFor="project-agent-notes">Agent notes</label>
            <textarea
              id="project-agent-notes"
              className="textarea"
              value={contextDraft.agent_notes}
              onChange={(event) => setContextDraft((prev) => ({ ...prev, agent_notes: event.target.value }))}
            />
          </div>
          <div className="inline-actions">
            <button className="button" type="button" onClick={handleContextSave}>
              Save context
            </button>
          </div>
          {contextNotice ? <p className="subtle">{contextNotice}</p> : null}
          {contextError ? <p className="subtle">{contextError}</p> : null}
        </div>
      </Modal>

      <Modal
        isOpen={taskModalOpen}
        title={isOwner ? 'Edit Task' : 'Update Task Status'}
        onClose={() => setTaskModalOpen(false)}
      >
        {taskDraft ? (
          <div className="grid">
            {isOwner ? (
              <>
                <div className="field">
                  <label className="label" htmlFor="task-title">Title</label>
                  <input
                    id="task-title"
                    className="input"
                    value={taskDraft.title}
                    onChange={(event) => setTaskDraft((prev) => ({ ...prev, title: event.target.value }))}
                  />
                </div>
                <div className="field">
                  <label className="label" htmlFor="task-description">Description</label>
                  <textarea
                    id="task-description"
                    className="textarea"
                    value={taskDraft.description}
                    onChange={(event) => setTaskDraft((prev) => ({ ...prev, description: event.target.value }))}
                  />
                </div>
                <div className="grid two">
                  <div className="field">
                    <label className="label" htmlFor="task-category">Category</label>
                    <select
                      id="task-category"
                      className="select"
                      value={taskDraft.category}
                      onChange={(event) => setTaskDraft((prev) => ({ ...prev, category: event.target.value }))}
                    >
                      {TASK_CATEGORY_OPTIONS.map(([value, label]) => (
                        <option key={value} value={value}>{label}</option>
                      ))}
                    </select>
                  </div>
                  <div className="field">
                    <label className="label" htmlFor="task-priority">Priority</label>
                    <select
                      id="task-priority"
                      className="select"
                      value={taskDraft.priority}
                      onChange={(event) => setTaskDraft((prev) => ({ ...prev, priority: event.target.value }))}
                    >
                      {TASK_PRIORITY_OPTIONS.map(([value, label]) => (
                        <option key={value} value={value}>{label}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </>
            ) : null}

            <div className="field">
              <label className="label" htmlFor="task-status">Status</label>
              <select
                id="task-status"
                className="select"
                value={taskDraft.status}
                onChange={(event) => setTaskDraft((prev) => ({ ...prev, status: event.target.value }))}
              >
                {TASK_STATUS_OPTIONS.map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>

            {isOwner ? (
              <div className="grid two">
                <div className="field">
                  <label className="label" htmlFor="task-assignee">Assignee</label>
                  <select
                    id="task-assignee"
                    className="select"
                    value={taskDraft.assigned_to_id}
                    onChange={(event) => setTaskDraft((prev) => ({ ...prev, assigned_to_id: event.target.value }))}
                  >
                    <option value="">Unassigned</option>
                    {memberOptions.map(([value, label]) => (
                      <option key={value} value={value}>{label}</option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label className="label" htmlFor="task-finding">Related vulnerability</label>
                  <select
                    id="task-finding"
                    className="select"
                    value={taskDraft.related_finding_id}
                    onChange={(event) =>
                      setTaskDraft((prev) => ({ ...prev, related_finding_id: event.target.value }))
                    }
                  >
                    <option value="">None</option>
                    {vulnerabilityOptions.map(([value, label]) => (
                      <option key={value} value={value}>{label}</option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label className="label" htmlFor="task-due-date">Due date</label>
                  <input
                    id="task-due-date"
                    className="input"
                    type="date"
                    value={taskDraft.due_date}
                    onChange={(event) => setTaskDraft((prev) => ({ ...prev, due_date: event.target.value }))}
                  />
                </div>
              </div>
            ) : null}

            <div className="inline-actions">
              <button className="button" type="button" onClick={handleTaskSave}>
                Save task
              </button>
            </div>
            {taskError ? <p className="subtle">{taskError}</p> : null}
          </div>
        ) : null}
      </Modal>

      <Modal
        isOpen={inviteModalOpen}
        title="Invite Member"
        onClose={() => setInviteModalOpen(false)}
      >
        <div className="grid">
          <div className="field">
            <label className="label">Search users</label>
            <div className="inline-actions">
              <input
                className="input"
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="Username or email..."
              />
              <button className="button" type="button" onClick={handleSearch}>
                Search
              </button>
            </div>
          </div>

          {searchError ? <p className="subtle">{searchError}</p> : null}

          <div className="repo-list compact-list">
            {searchResults.map((result) => (
              <div
                key={result.id}
                className={`repo-item ${String(inviteUserId) === String(result.id) ? 'selected' : ''}`}
              >
                <div className="repo-info">
                  <span className="repo-name">{result.name || result.username}</span>
                  <span className="repo-meta">@{result.username}</span>
                </div>
                <button
                  className={`button compact ${String(inviteUserId) === String(result.id) ? '' : 'ghost'}`}
                  type="button"
                  onClick={() => setInviteUserId(result.id)}
                >
                  {String(inviteUserId) === String(result.id) ? 'Selected' : 'Select'}
                </button>
              </div>
            ))}
          </div>

          <div className="grid two">
            <div className="field">
              <label className="label" htmlFor="invite-display-role">Display role</label>
              <select
                id="invite-display-role"
                className="select"
                value={inviteDisplayRole}
                onChange={(event) => setInviteDisplayRole(event.target.value)}
              >
                {DISPLAY_ROLE_OPTIONS.map((role) => (
                  <option key={role} value={role}>{role}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label className="label" htmlFor="invite-roles">Access tags</label>
              <input
                id="invite-roles"
                className="input"
                value={inviteRolesText}
                onChange={(event) => setInviteRolesText(event.target.value)}
              />
            </div>
          </div>

          <div className="tag-row">
            {ROLE_TAG_OPTIONS.map((role) => (
              <button
                key={role}
                className={`tag-button ${toList(inviteRolesText).includes(role) ? 'active' : ''}`}
                type="button"
                onClick={() => setInviteRolesText((prev) => toggleTextTag(prev, role))}
              >
                {role}
              </button>
            ))}
          </div>

          <button className="button" type="button" style={{ width: '100%' }} onClick={handleInvite}>
            Add member
          </button>
          {inviteNotice ? <p className="subtle">{inviteNotice}</p> : null}
        </div>
      </Modal>

      <Modal
        isOpen={memberModalOpen}
        title="Manage Member"
        onClose={() => setMemberModalOpen(false)}
      >
        {memberDraft ? (
          <div className="grid">
            <div className="profile-row">
              <div className="avatar small">{selectedMember?.username?.[0]?.toUpperCase() || 'U'}</div>
              <div>
                <strong>{selectedMember?.name || selectedMember?.username}</strong>
                <p className="subtle">@{selectedMember?.username}</p>
              </div>
            </div>
            <div className="grid two">
              <div className="field">
                <label className="label" htmlFor="member-display-role">Display role</label>
                <select
                  id="member-display-role"
                  className="select"
                  value={memberDraft.display_role}
                  onChange={(event) => setMemberDraft((prev) => ({ ...prev, display_role: event.target.value }))}
                >
                  {DISPLAY_ROLE_OPTIONS.map((role) => (
                    <option key={role} value={role}>{role}</option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label className="label" htmlFor="member-roles">Access tags</label>
                <input
                  id="member-roles"
                  className="input"
                  value={memberDraft.roles}
                  onChange={(event) => setMemberDraft((prev) => ({ ...prev, roles: event.target.value }))}
                />
              </div>
            </div>
            <div className="tag-row">
              {ROLE_TAG_OPTIONS.map((role) => (
                <button
                  key={role}
                  className={`tag-button ${toList(memberDraft.roles).includes(role) ? 'active' : ''}`}
                  type="button"
                  onClick={() =>
                    setMemberDraft((prev) => ({ ...prev, roles: toggleTextTag(prev.roles, role) }))
                  }
                >
                  {role}
                </button>
              ))}
            </div>
            <div className="inline-actions">
              <button className="button" type="button" onClick={handleMemberSave}>
                Save member
              </button>
              <button
                className="button ghost danger"
                type="button"
                onClick={() => handleRemoveMember(selectedMember)}
              >
                Remove member
              </button>
            </div>
            {memberError ? <p className="subtle">{memberError}</p> : null}
          </div>
        ) : null}
      </Modal>

      <Modal
        isOpen={meetingModalOpen}
        title="Meeting Settings"
        onClose={() => setMeetingModalOpen(false)}
      >
        {meetingDraft ? (
          <div className="grid">
            <div className="grid two">
              <div className="field">
                <label className="label" htmlFor="meeting-days">Meeting days</label>
                <select
                  id="meeting-days"
                  className="select"
                  multiple
                  size="5"
                  value={meetingDraft.meeting_days}
                  onChange={(event) =>
                    setMeetingDraft((prev) => ({ ...prev, meeting_days: selectValues(event) }))
                  }
                >
                  {WEEKDAY_OPTIONS.map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label className="label" htmlFor="meeting-time">Meeting time</label>
                <select
                  id="meeting-time"
                  className="select"
                  value={meetingDraft.meeting_time}
                  onChange={(event) => setMeetingDraft((prev) => ({ ...prev, meeting_time: event.target.value }))}
                >
                  {timeOptions.map((value) => (
                    <option key={value} value={value}>{formatTimeLabel(value)}</option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label className="label" htmlFor="meeting-timezone">Timezone</label>
                <select
                  id="meeting-timezone"
                  className="select"
                  value={meetingDraft.timezone}
                  onChange={(event) => setMeetingDraft((prev) => ({ ...prev, timezone: event.target.value }))}
                >
                  {TIMEZONE_OPTIONS.map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label className="label" htmlFor="meeting-alert">Reminder</label>
                <select
                  id="meeting-alert"
                  className="select"
                  value={meetingDraft.alert_minutes_before}
                  onChange={(event) =>
                    setMeetingDraft((prev) => ({
                      ...prev,
                      alert_minutes_before: Number(event.target.value),
                    }))
                  }
                >
                  {ALERT_OPTIONS.map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="field">
              <label className="label" htmlFor="meeting-active">Status</label>
              <select
                id="meeting-active"
                className="select"
                value={meetingDraft.is_active ? 'true' : 'false'}
                onChange={(event) =>
                  setMeetingDraft((prev) => ({ ...prev, is_active: event.target.value === 'true' }))
                }
              >
                <option value="true">Active</option>
                <option value="false">Paused</option>
              </select>
            </div>
            <div className="field">
              <label className="label" htmlFor="meeting-link">Google Meet link</label>
              <input
                id="meeting-link"
                className="input"
                value={meetingDraft.google_meet_link}
                onChange={(event) =>
                  setMeetingDraft((prev) => ({ ...prev, google_meet_link: event.target.value }))
                }
                placeholder="https://meet.google.com/..."
              />
            </div>
            <div className="field">
              <label className="label" htmlFor="meeting-weekly-goals">Weekly goals</label>
              <textarea
                id="meeting-weekly-goals"
                className="textarea"
                value={meetingDraft.weekly_goals}
                onChange={(event) => setMeetingDraft((prev) => ({ ...prev, weekly_goals: event.target.value }))}
              />
            </div>
            <div className="field">
              <label className="label" htmlFor="meeting-monthly-goals">Monthly goals</label>
              <textarea
                id="meeting-monthly-goals"
                className="textarea"
                value={meetingDraft.monthly_goals}
                onChange={(event) => setMeetingDraft((prev) => ({ ...prev, monthly_goals: event.target.value }))}
              />
            </div>
            <div className="inline-actions">
              <button className="button" type="button" onClick={handleMeetingSave}>
                Save settings
              </button>
            </div>
            {meetingNotice ? <p className="subtle">{meetingNotice}</p> : null}
            {meetingError ? <p className="subtle">{meetingError}</p> : null}
          </div>
        ) : null}
      </Modal>
    </div>
  );
}
