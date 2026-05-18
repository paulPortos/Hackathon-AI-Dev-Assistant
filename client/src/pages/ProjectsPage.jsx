import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import { api } from '../api';
import { normalizeList } from '../api/client';
import SectionCard from '../components/SectionCard';
import { GitHubIcon } from '../components/Icons';

export default function ProjectsPage() {
  const [projects, setProjects] = useState([]);
  const [repositories, setRepositories] = useState([]);
  const [status, setStatus] = useState('idle');
  const [repoStatus, setRepoStatus] = useState('idle');
  const [error, setError] = useState('');
  const [repoError, setRepoError] = useState('');
  const [importNotice, setImportNotice] = useState('');
  const [importError, setImportError] = useState('');
  const [filter, setFilter] = useState('');

  const loadProjects = async () => {
    setStatus('loading');
    setError('');
    try {
      const payload = await api.listProjects();
      setProjects(normalizeList(payload));
      setStatus('ready');
    } catch (err) {
      setStatus('error');
      setError(err.message);
    }
  };

  const loadRepositories = async () => {
    setRepoStatus('loading');
    setRepoError('');
    try {
      const payload = await api.listGithubRepositories();
      setRepositories(normalizeList(payload));
      setRepoStatus('ready');
    } catch (err) {
      setRepoStatus('error');
      setRepoError(err.message);
    }
  };

  useEffect(() => {
    loadProjects();
    loadRepositories();
  }, []);

  const handleImport = async (repository) => {
    setImportNotice('');
    setImportError('');
    if (!repository) {
      setImportError('Repository is required.');
      return;
    }
    try {
      const project = await api.importProjectFromGithub({ repository });
      setProjects((prev) => [project, ...prev]);
      setImportNotice(`Successfully imported ${repository}`);
      setTimeout(() => setImportNotice(''), 5000);
    } catch (err) {
      setImportError(err.message);
    }
  };

  const filteredRepos = useMemo(() => {
    if (!filter) return repositories;
    return repositories.filter(repo => 
      repo.full_name.toLowerCase().includes(filter.toLowerCase())
    );
  }, [repositories, filter]);

  return (
    <div className="grid">
      <section className="hero">
        <div className="hero-card">
          <h1>Project Workspace</h1>
          <p>
            Manage your synchronized GitHub repositories. You can monitor code health,
            run security audits, and collaborate with your senior AI developers here.
          </p>
          
          {importNotice && (
            <div className="pill" style={{ background: '#e8f5e9', color: '#2e7d32', marginTop: '16px' }}>
              {importNotice}
            </div>
          )}
          {importError && (
            <div className="pill" style={{ background: '#ffebee', color: '#c62828', marginTop: '16px' }}>
              {importError}
            </div>
          )}
        </div>

        <SectionCard title="Import Repository" eyebrow="GitHub Integration">
          <p className="subtle">Select a repository to begin monitoring from your GitHub account.</p>
          
          <div className="field">
            <input
              className="input"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              placeholder="Search your repositories..."
            />
          </div>

          <div className="repo-list">
            {repoStatus === 'loading' ? (
              <p className="subtle" style={{ padding: '20px', textAlign: 'center' }}>Loading GitHub repositories...</p>
            ) : repoStatus === 'error' ? (
              <p className="subtle" style={{ padding: '20px', textAlign: 'center', color: '#c62828' }}>
                Error loading repositories: {repoError}
              </p>
            ) : filteredRepos.length > 0 ? (
              filteredRepos.map((repo) => (
                <div key={repo.github_repo_id || repo.id} className="repo-item">
                  <div className="repo-info">
                    <span className="repo-name">{repo.full_name}</span>
                    <span className="repo-meta">{repo.primary_language || 'No language'} • {repo.visibility}</span>
                  </div>
                  <button 
                    className="button secondary" 
                    style={{ padding: '6px 12px', fontSize: '12px' }}
                    onClick={() => handleImport(repo.full_name)}
                  >
                    Import
                  </button>
                </div>
              ))
            ) : (
              <p className="subtle" style={{ padding: '20px', textAlign: 'center' }}>No repositories found.</p>
            )}
          </div>
        </SectionCard>
      </section>

      <div className="auth-divider">Your Active Projects</div>

      <section className="grid three">
        {status === 'loading' ? (
          <p className="subtle">Syncing projects...</p>
        ) : status === 'error' ? (
          <div className="section-card" style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '48px' }}>
            <h3>Failed to load projects</h3>
            <p className="subtle">{error}</p>
          </div>
        ) : projects.length > 0 ? (
          projects.map((project) => (
            <SectionCard key={project.id} title={project.github_full_name} eyebrow="Project">
              <p style={{ minHeight: '4.5em', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                {project.overview || project.github_description || 'No overview yet.'}
              </p>
              <div className="inline-actions">
                <span className="tag">{project.github_primary_language || 'Unknown'}</span>
                <span className="tag">{project.github_visibility}</span>
              </div>
              <div className="inline-actions" style={{ marginTop: 'auto', paddingTop: '16px' }}>
                <Link className="button" to={`/projects/${project.id}`}>
                  Open
                </Link>
                <a className="button ghost" href={project.github_html_url} target="_blank" rel="noreferrer">
                  <GitHubIcon size={14} />
                </a>
              </div>
            </SectionCard>
          ))
        ) : (
          <div className="section-card" style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '48px' }}>
            <h3>No projects yet</h3>
            <p className="subtle">Import your first repository from the list above.</p>
          </div>
        )}
      </section>
    </div>
  );
}
