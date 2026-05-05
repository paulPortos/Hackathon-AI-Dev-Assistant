import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { api } from '../api';
import { normalizeList } from '../api/client';
import Modal from '../components/Modal';
import SectionCard from '../components/SectionCard';
import { GitHubIcon } from '../components/Icons';

const toList = (value) =>
  value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);

export default function ProjectPage() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [members, setMembers] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [vulnerabilities, setVulnerabilities] = useState([]);
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState('');
  const [isMocked, setIsMocked] = useState(false);

  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchError, setSearchError] = useState('');

  const [inviteUserId, setInviteUserId] = useState('');
  const [inviteDisplayRole, setInviteDisplayRole] = useState('Contributor');
  const [inviteRolesText, setInviteRolesText] = useState('frontend, security');
  const [inviteNotice, setInviteNotice] = useState('');

  const [profileModalOpen, setProfileModalOpen] = useState(false);
  const [profileUser, setProfileUser] = useState(null);
  const [profileDescription, setProfileDescription] = useState(null);
  const [profileError, setProfileError] = useState('');

  const [inviteModalOpen, setInviteModalOpen] = useState(false);
  const [meetingModalOpen, setMeetingModalOpen] = useState(false);
  const [meetingDraft, setMeetingDraft] = useState(null);
  const [meetingNotice, setMeetingNotice] = useState('');
  const [meetingError, setMeetingError] = useState('');

  const meetingDefaults = useMemo(
    () => ({
      meeting_days: 'monday, thursday',
      meeting_time: '09:30:00',
      timezone: 'America/Los_Angeles',
      google_meet_link: '',
      weekly_goals: '',
      monthly_goals: '',
      alert_minutes_before: 30,
      is_active: true,
    }),
    []
  );

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

  const handleSearch = async () => {
    setSearchError('');
    setInviteNotice('');
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
      setInviteNotice('Invite sent.');
    } catch (err) {
      setSearchError(err.message);
    }
  };

  const openProfileModal = async (userId) => {
    setProfileModalOpen(true);
    setProfileError('');
    try {
      const [userPayload, descriptionPayload] = await Promise.all([
        api.getUser(userId),
        api.getUserDescriptionForUser(userId),
      ]);
      setProfileUser(userPayload);
      setProfileDescription(descriptionPayload);
    } catch (err) {
      setProfileUser(null);
      setProfileDescription(null);
      setProfileError(err.message);
    }
  };

  const openMeetingModal = async () => {
    setMeetingModalOpen(true);
    setMeetingError('');
    setMeetingNotice('');
    try {
      const settings = await api.getMeetingSettings(projectId);
      setMeetingDraft({
        meeting_days: (settings.meeting_days || []).join(', '),
        meeting_time: settings.meeting_time || '',
        timezone: settings.timezone || '',
        google_meet_link: settings.google_meet_link || '',
        weekly_goals: settings.weekly_goals || '',
        monthly_goals: settings.monthly_goals || '',
        alert_minutes_before: settings.alert_minutes_before || 0,
        is_active: settings.is_active,
      });
    } catch (err) {
      setMeetingDraft(meetingDefaults);
      setMeetingError(err.message);
    }
  };

  const handleMeetingSave = async () => {
    setMeetingError('');
    setMeetingNotice('');
    try {
      const payload = {
        meeting_days: toList(meetingDraft.meeting_days),
        meeting_time: meetingDraft.meeting_time,
        timezone: meetingDraft.timezone,
        google_meet_link: meetingDraft.google_meet_link,
        weekly_goals: meetingDraft.weekly_goals,
        monthly_goals: meetingDraft.monthly_goals,
        alert_minutes_before: Number(meetingDraft.alert_minutes_before) || 0,
        is_active: Boolean(meetingDraft.is_active),
      };
      await api.updateMeetingSettings(projectId, payload, 'PATCH');
      setMeetingNotice('Meeting settings saved.');
    } catch (err) {
      setMeetingError(err.message);
    }
  };

  return (
    <div className="grid">
      <section className="grid two" style={{ alignItems: 'stretch' }}>
        <SectionCard 
          title="Project Workspace"
          actions={project ? (
            <>
              <Link className="button ghost" to="/projects" style={{ padding: '8px 16px' }}>
                Back to projects
              </Link>
              <button className="button ghost" type="button" onClick={openMeetingModal} style={{ padding: '8px 16px' }}>
                Meeting settings
              </button>
              <Link className="button secondary" to={`/senior?projectId=${project.id}`} style={{ padding: '8px 24px' }}>
                Report to senior
              </Link>
            </>
          ) : null}
        >
          <p className="subtle" style={{ marginBottom: '16px' }}>
            View vulnerabilities, tasks, and members. Invite new contributors and
            configure meeting settings.
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
              </div>
            </div>
          )}
        </SectionCard>

        <SectionCard title="Project Context">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div>
              <p className="subtle" style={{ fontWeight: 600, fontSize: '12px', textTransform: 'uppercase', marginBottom: '4px' }}>Goals</p>
              <p style={{ margin: 0 }}>{project?.goals || 'No goals defined yet.'}</p>
            </div>
            <div>
              <p className="subtle" style={{ fontWeight: 600, fontSize: '12px', textTransform: 'uppercase', marginBottom: '4px' }}>Tech Stack</p>
              <p style={{ margin: 0 }}>{(project?.tech_stack || []).join(', ') || '---'}</p>
            </div>
            <div>
              <p className="subtle" style={{ fontWeight: 600, fontSize: '12px', textTransform: 'uppercase', marginBottom: '4px' }}>Business Context</p>
              <p style={{ margin: 0 }}>{project?.business_context || '---'}</p>
            </div>
          </div>
        </SectionCard>
      </section>

      <section className="grid two">
        <SectionCard title="Vulnerabilities">
          <div className="scroll-area" style={{ height: '320px', overflowY: 'auto', paddingRight: '8px' }}>
            <ul className="list">
              {vulnerabilities.map((vulnerability) => (
                <li key={vulnerability.id}>
                  <strong>{vulnerability.title}</strong>
                  <p className="subtle">{vulnerability.summary}</p>
                  <div className="inline-actions">
                    <span className="tag">{vulnerability.severity}</span>
                    <span className="tag">{vulnerability.status}</span>
                  </div>
                </li>
              ))}
              {vulnerabilities.length === 0 && <p className="subtle">No vulnerabilities reported.</p>}
            </ul>
          </div>
        </SectionCard>
        <SectionCard title="Tasks">
          <div className="scroll-area" style={{ height: '320px', overflowY: 'auto', paddingRight: '8px' }}>
            <ul className="list">
              {tasks.map((task) => (
                <li key={task.id}>
                  <strong>{task.title}</strong>
                  <p className="subtle">{task.description}</p>
                  <div className="inline-actions">
                    <span className="tag">{task.priority}</span>
                    <span className="tag">{task.status}</span>
                  </div>
                </li>
              ))}
              {tasks.length === 0 && <p className="subtle">No tasks assigned.</p>}
            </ul>
          </div>
        </SectionCard>
      </section>

      <section className="grid">
        <SectionCard 
          title="Members" 
          actions={
            <button className="button" type="button" onClick={() => setInviteModalOpen(true)}>
              Invite Member
            </button>
          }
        >
          <ul className="list">
            {members.map((member) => (
              <li key={member.id}>
                <div className="inline-actions">
                  <span className="tag">{member.display_role}</span>
                  <button
                    className="button ghost"
                    type="button"
                    onClick={() => openProfileModal(member.user_id)}
                  >
                    View profile
                  </button>
                </div>
                <p className="subtle">{member.name || member.username}</p>
              </li>
            ))}
            {members.length === 0 && <p className="subtle">No members in this project yet.</p>}
          </ul>
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
                <p className="subtle">{profileUser.username}</p>
              </div>
            </div>
            {profileDescription ? (
              <div>
                <p className="subtle">{profileDescription.summary}</p>
                <p className="subtle">
                  Role: {profileDescription.primary_role} ({profileDescription.experience_level})
                </p>
              </div>
            ) : null}
          </div>
        ) : (
          <p className="subtle">Select a user to load their profile.</p>
        )}
      </Modal>

      <Modal
        isOpen={inviteModalOpen}
        title="Invite Member"
        onClose={() => setInviteModalOpen(false)}
      >
        <div className="grid">
          <div className="field">
            <label className="label">Search Users</label>
            <div className="inline-actions">
              <input
                className="input"
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="Username or name..."
              />
              <button className="button" type="button" onClick={handleSearch}>
                Search
              </button>
            </div>
          </div>
          
          {searchError && <p className="subtle" style={{ color: 'var(--accent-500)' }}>{searchError}</p>}
          
          <div className="repo-list" style={{ maxHeight: '200px', overflowY: 'auto', marginBottom: '16px' }}>
            {searchResults.map((result) => (
              <div key={result.id} className="repo-item" style={{ padding: '8px', border: inviteUserId === result.id ? '2px solid var(--accent-500)' : '1px solid rgba(0,0,0,0.05)' }}>
                <div className="repo-info">
                  <span className="repo-name">{result.name || result.username}</span>
                  <span className="repo-meta">@{result.username}</span>
                </div>
                <button
                  className={`button ${inviteUserId === result.id ? '' : 'ghost'}`}
                  style={{ padding: '4px 12px', fontSize: '12px' }}
                  type="button"
                  onClick={() => setInviteUserId(result.id)}
                >
                  {inviteUserId === result.id ? 'Selected' : 'Select'}
                </button>
              </div>
            ))}
          </div>

          <div className="field">
            <label className="label">Display Role</label>
            <input
              className="input"
              value={inviteDisplayRole}
              onChange={(event) => setInviteDisplayRole(event.target.value)}
              placeholder="e.g. Lead Developer"
            />
          </div>
          <div className="field">
            <label className="label">Access Tags (comma separated)</label>
            <input
              className="input"
              value={inviteRolesText}
              onChange={(event) => setInviteRolesText(event.target.value)}
              placeholder="frontend, backend, admin"
            />
          </div>
          
          <button className="button" type="button" style={{ width: '100%' }} onClick={handleInvite}>
            Send Invitation
          </button>
          
          {inviteNotice && <p className="pill" style={{ background: 'var(--accent-100)', textAlign: 'center', marginTop: '12px' }}>{inviteNotice}</p>}
        </div>
      </Modal>

      <Modal
        isOpen={meetingModalOpen}
        title="Meeting Settings"
        onClose={() => setMeetingModalOpen(false)}
      >
        <div className="grid">
          <div className="field">
            <label className="label" htmlFor="meeting-days">
              Meeting days (full names)
            </label>
            <input
              id="meeting-days"
              className="input"
              value={meetingDraft?.meeting_days || ''}
              onChange={(event) =>
                setMeetingDraft((prev) => ({ ...prev, meeting_days: event.target.value }))
              }
            />
          </div>
          <div className="field">
            <label className="label" htmlFor="meeting-time">
              Meeting time (HH:MM:SS)
            </label>
            <input
              id="meeting-time"
              className="input"
              value={meetingDraft?.meeting_time || ''}
              onChange={(event) =>
                setMeetingDraft((prev) => ({ ...prev, meeting_time: event.target.value }))
              }
            />
          </div>
          <div className="field">
            <label className="label" htmlFor="meeting-timezone">
              Timezone (IANA)
            </label>
            <input
              id="meeting-timezone"
              className="input"
              value={meetingDraft?.timezone || ''}
              onChange={(event) =>
                setMeetingDraft((prev) => ({ ...prev, timezone: event.target.value }))
              }
              placeholder="America/Los_Angeles"
            />
          </div>
          <div className="field">
            <label className="label" htmlFor="meeting-link">
              Google Meet link
            </label>
            <input
              id="meeting-link"
              className="input"
              value={meetingDraft?.google_meet_link || ''}
              onChange={(event) =>
                setMeetingDraft((prev) => ({ ...prev, google_meet_link: event.target.value }))
              }
            />
          </div>
          <div className="field">
            <label className="label" htmlFor="meeting-weekly-goals">
              Weekly goals
            </label>
            <textarea
              id="meeting-weekly-goals"
              className="textarea"
              value={meetingDraft?.weekly_goals || ''}
              onChange={(event) =>
                setMeetingDraft((prev) => ({ ...prev, weekly_goals: event.target.value }))
              }
            />
          </div>
          <div className="field">
            <label className="label" htmlFor="meeting-monthly-goals">
              Monthly goals
            </label>
            <textarea
              id="meeting-monthly-goals"
              className="textarea"
              value={meetingDraft?.monthly_goals || ''}
              onChange={(event) =>
                setMeetingDraft((prev) => ({ ...prev, monthly_goals: event.target.value }))
              }
            />
          </div>
          <div className="field">
            <label className="label" htmlFor="meeting-alert">
              Alert minutes before
            </label>
            <input
              id="meeting-alert"
              className="input"
              type="number"
              value={meetingDraft?.alert_minutes_before || 0}
              onChange={(event) =>
                setMeetingDraft((prev) => ({
                  ...prev,
                  alert_minutes_before: event.target.value,
                }))
              }
            />
          </div>
          <div className="field">
            <label className="label" htmlFor="meeting-active">
              Active
            </label>
            <select
              id="meeting-active"
              className="select"
              value={meetingDraft?.is_active ? 'true' : 'false'}
              onChange={(event) =>
                setMeetingDraft((prev) => ({
                  ...prev,
                  is_active: event.target.value === 'true',
                }))
              }
            >
              <option value="true">Active</option>
              <option value="false">Paused</option>
            </select>
          </div>
          <div className="inline-actions">
            <button className="button" type="button" onClick={handleMeetingSave}>
              Save settings
            </button>
          </div>
          {meetingNotice ? <p className="subtle">{meetingNotice}</p> : null}
          {meetingError ? <p className="subtle">{meetingError}</p> : null}
        </div>
      </Modal>
    </div>
  );
}
