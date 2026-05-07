import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import { api } from '../api';
import { normalizeList } from '../api/client';
import SectionCard from '../components/SectionCard';
import { GitHubIcon } from '../components/Icons';

const CLOSED_TASK_STATUSES = new Set(['completed', 'canceled']);
const CLOSED_VULNERABILITY_STATUSES = new Set(['resolved', 'dismissed']);

const isOpenTask = (task) => !CLOSED_TASK_STATUSES.has(String(task.status || '').toLowerCase());

const isOpenCriticalFinding = (vulnerability) => {
  const severity = String(vulnerability.severity || '').toLowerCase();
  const status = String(vulnerability.status || '').toLowerCase();
  return severity === 'critical' && !CLOSED_VULNERABILITY_STATUSES.has(status);
};

export default function HomePage() {
  const [projects, setProjects] = useState([]);
  const [stats, setStats] = useState({
    criticalFindings: 0,
    seniorSessions: 0,
    openTasks: 0,
  });
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState('');

  const loadOverview = async () => {
    setStatus('loading');
    setError('');

    try {
      const projectList = normalizeList(await api.listProjects());
      const detailErrors = [];

      const fetchList = async (loader, label) => {
        try {
          return normalizeList(await loader());
        } catch (err) {
          detailErrors.push(label);
          return [];
        }
      };

      const [sessions, projectTasks, projectVulnerabilities] = await Promise.all([
        fetchList(() => api.listSeniorSessions(), 'senior sessions'),
        Promise.all(
          projectList.map((project) =>
            fetchList(() => api.listProjectTasks(project.id), `tasks for ${project.github_full_name || project.id}`)
          )
        ).then((results) => results.flat()),
        Promise.all(
          projectList.map((project) =>
            fetchList(
              () => api.listProjectVulnerabilities(project.id),
              `findings for ${project.github_full_name || project.id}`
            )
          )
        ).then((results) => results.flat()),
      ]);

      setProjects(projectList);
      setStats({
        criticalFindings: projectVulnerabilities.filter(isOpenCriticalFinding).length,
        seniorSessions: sessions.length,
        openTasks: projectTasks.filter(isOpenTask).length,
      });
      setStatus(detailErrors.length ? 'partial' : 'ready');
      setError(
        detailErrors.length
          ? `Some overview details could not load: ${detailErrors.slice(0, 3).join(', ')}.`
          : ''
      );
    } catch (err) {
      setProjects([]);
      setStats({
        criticalFindings: 0,
        seniorSessions: 0,
        openTasks: 0,
      });
      setStatus('error');
      setError(err.message);
    }
  };

  useEffect(() => {
    loadOverview();
  }, []);

  const projectCount = projects.length;
  const featuredProjects = useMemo(() => projects.slice(0, 3), [projects]);
  const apiOnline = status !== 'error';

  return (
    <div className="grid">
      <section className="hero">
        <div className="hero-card">
          <div className="pill">Workspace Overview</div>
          <h1>Welcome back to Visor</h1>
          <p>
            You have {projectCount} active projects. Use Visor to review recent
            findings, check open work, and ask the Senior AI agent to verify code
            changes before your next demo.
          </p>
          <div className="inline-actions">
            <Link className="button" to="/projects">
              Go to Projects
            </Link>
            <Link className="button ghost" to="/senior">
              Start Senior Session
            </Link>
          </div>
          {status === 'loading' && <p className="subtle">Updating workspace...</p>}
          {error ? <p className="subtle">{error}</p> : null}
        </div>

        <SectionCard title="System Status" eyebrow="Live checks">
          <div style={{ display: 'grid', gap: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span className="subtle">API Connection</span>
              <span
                className="tag"
                style={{
                  background: apiOnline ? '#e8f5e9' : '#ffebee',
                  color: apiOnline ? '#2e7d32' : '#c62828',
                }}
              >
                {apiOnline ? 'Online' : 'Needs attention'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span className="subtle">GitHub Projects</span>
              <span className="tag">{projectCount ? 'Synced' : 'Ready'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span className="subtle">Senior Agent</span>
              <span className="tag">{stats.seniorSessions ? 'Active' : 'Ready'}</span>
            </div>
          </div>
          <div style={{ marginTop: '20px' }}>
            <Link className="button secondary" style={{ width: '100%' }} to="/profile">
              Account Settings
            </Link>
          </div>
        </SectionCard>
      </section>

      <section className="stat-grid">
        <div className="stat-card">
          <p className="subtle">Total Projects</p>
          <div className="stat-value">{projectCount}</div>
        </div>
        <div className="stat-card">
          <p className="subtle">Critical Findings</p>
          <div className="stat-value" style={{ color: stats.criticalFindings ? '#d32f2f' : undefined }}>
            {stats.criticalFindings}
          </div>
        </div>
        <div className="stat-card">
          <p className="subtle">Senior Sessions</p>
          <div className="stat-value">{stats.seniorSessions}</div>
        </div>
        <div className="stat-card">
          <p className="subtle">Open Tasks</p>
          <div className="stat-value">{stats.openTasks}</div>
        </div>
      </section>

      <div className="auth-divider">Recent Projects</div>

      {status === 'loading' ? <p className="subtle">Loading recent projects...</p> : null}
      {status !== 'idle' && status !== 'loading' && featuredProjects.length === 0 ? (
        <SectionCard title="No projects yet" eyebrow="GitHub">
          <p className="subtle">Import a repository to start reviewing code with Visor.</p>
          <Link className="button" to="/projects">
            Import Repository
          </Link>
        </SectionCard>
      ) : null}

      {featuredProjects.length > 0 ? (
        <section className="grid three">
          {featuredProjects.map((project) => (
            <SectionCard key={project.id} title={project.github_full_name} eyebrow="Recently Updated">
              <p style={{ minHeight: '4.5em', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                {project.overview || project.github_description || 'No overview yet.'}
              </p>
              <div className="inline-actions">
                <span className="tag">{project.github_primary_language || 'Unknown'}</span>
              </div>
              <div className="inline-actions" style={{ marginTop: 'auto', paddingTop: '16px' }}>
                <Link className="button" to={`/projects/${project.id}`}>
                  View Details
                </Link>
                <a className="button ghost" href={project.github_html_url} target="_blank" rel="noreferrer">
                  <GitHubIcon size={14} />
                </a>
              </div>
            </SectionCard>
          ))}
        </section>
      ) : null}
    </div>
  );
}
