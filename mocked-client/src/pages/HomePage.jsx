import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import { api } from '../api';
import { normalizeList } from '../api/client';
import { mockProjects } from '../api/mockData';
import SectionCard from '../components/SectionCard';
import { GitHubIcon } from '../components/Icons';

export default function HomePage() {
  const [projects, setProjects] = useState([]);
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState('');
  const [isMocked, setIsMocked] = useState(false);

  const loadProjects = async () => {
    setStatus('loading');
    setError('');
    try {
      const payload = await api.listProjects();
      setProjects(normalizeList(payload));
      setIsMocked(false);
      setStatus('ready');
    } catch (err) {
      setProjects(mockProjects);
      setIsMocked(true);
      setStatus('mocked');
      setError(err.message);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const projectCount = projects.length;
  const featuredProjects = useMemo(() => projects.slice(0, 3), [projects]);

  return (
    <div className="grid">
      <section className="hero">
        <div className="hero-card">
          <div className="pill">Workspace Overview</div>
          <h1>Welcome back to Khaki</h1>
          <p>
            You have {projectCount} active projects. Use the dashboard to monitor
            recent security findings, chat with your senior AI developer, or sync
            new repositories from GitHub.
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
        </div>
        
        <SectionCard title="System Status" eyebrow="Real-time">
          <div style={{ display: 'grid', gap: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span className="subtle">API Connection</span>
              <span className="tag" style={{ background: '#e8f5e9', color: '#2e7d32' }}>Online</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span className="subtle">GitHub Sync</span>
              <span className="tag" style={{ background: '#e8f5e9', color: '#2e7d32' }}>Active</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span className="subtle">Senior Agent</span>
              <span className="tag">Ready</span>
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
          <div className="stat-value" style={{ color: '#d32f2f' }}>0</div>
        </div>
        <div className="stat-card">
          <p className="subtle">Senior Sessions</p>
          <div className="stat-value">4</div>
        </div>
        <div className="stat-card">
          <p className="subtle">Code Coverage</p>
          <div className="stat-value">82%</div>
        </div>
      </section>

      <div className="auth-divider">Recent Projects</div>

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
    </div>
  );
}
