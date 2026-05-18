import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { api } from '../api';
import { useAuth } from '../auth/AuthContext';
import SectionCard from '../components/SectionCard';

const emptyProfileForm = {
  primary_role: '',
  experience_level: '',
  summary: '',
  preferred_tasks: '',
  avoided_tasks: '',
  availability_notes: '',
  agent_notes: '',
};

const splitList = (value) =>
  value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);

const applyDescription = (description) => ({
  primary_role: description.primary_role || '',
  experience_level: description.experience_level || '',
  summary: description.summary || '',
  preferred_tasks: (description.preferred_tasks || []).join(', '),
  avoided_tasks: (description.avoided_tasks || []).join(', '),
  availability_notes: description.availability_notes || '',
  agent_notes: description.agent_notes || '',
});

export default function ProfilePage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(user || null);
  const [skills, setSkills] = useState([]);
  const [form, setForm] = useState(emptyProfileForm);
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const loadProfile = async () => {
    setStatus('loading');
    setError('');
    setNotice('');
    try {
      const mePayload = await api.me();
      setProfile(mePayload);

      try {
        const descriptionPayload = await api.getUserDescriptionMe();
        setSkills(descriptionPayload.skills || []);
        setForm(applyDescription(descriptionPayload));
      } catch {
        setSkills([]);
        setForm(emptyProfileForm);
        setNotice('Add your profile details so Visor can assign work more accurately.');
      }

      setStatus('ready');
    } catch (err) {
      setProfile(null);
      setSkills([]);
      setForm(emptyProfileForm);
      setStatus('error');
      setError(err.message);
    }
  };

  useEffect(() => {
    loadProfile();
  }, []);

  const updateSkill = (index, key, value) => {
    setSkills((prev) =>
      prev.map((skill, skillIndex) =>
        skillIndex === index ? { ...skill, [key]: value } : skill
      )
    );
  };

  const addSkill = () => {
    setSkills((prev) => [...prev, { name: '', level: 3 }]);
  };

  const removeSkill = (index) => {
    setSkills((prev) => prev.filter((_, skillIndex) => skillIndex !== index));
  };

  const handleSave = async () => {
    setNotice('');
    setError('');
    try {
      const payload = {
        primary_role: form.primary_role,
        experience_level: form.experience_level,
        summary: form.summary,
        skills: skills.filter((skill) => skill.name),
        preferred_tasks: splitList(form.preferred_tasks),
        avoided_tasks: splitList(form.avoided_tasks),
        availability_notes: form.availability_notes,
        agent_notes: form.agent_notes,
      };
      const savedDescription = await api.updateUserDescriptionMe(payload);
      setSkills(savedDescription.skills || payload.skills);
      setForm(applyDescription(savedDescription));
      setNotice('Profile saved.');
    } catch (err) {
      setError(err.message);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/', { replace: true });
  };

  return (
    <div className="grid">
      <section className="hero">
        <div className="hero-card">
          <h1>Profile</h1>
          <p>Combine GitHub user info with your user description and preferences.</p>
          <div className="inline-actions">
            <button className="button ghost" type="button" onClick={handleLogout}>
              Logout
            </button>
          </div>
          {status === 'loading' ? <p className="subtle">Loading profile...</p> : null}
          {error ? <p className="subtle">{error}</p> : null}
          {notice ? <p className="subtle">{notice}</p> : null}
          {profile ? (
            <div className="profile-row">
              <div className="avatar">{profile.username?.[0]?.toUpperCase() || 'U'}</div>
              <div>
                <strong>{profile.name || profile.username}</strong>
                <p className="subtle">{profile.email || 'No email on file'}</p>
              </div>
            </div>
          ) : null}
        </div>
        <SectionCard title="Quick status" eyebrow="User info">
          <p>GitHub ID: {profile?.github_id || '---'}</p>
          <p>Account: {profile?.username || '---'}</p>
          <p>Last updated: {profile?.updated_at || '---'}</p>
        </SectionCard>
      </section>

      <section className="grid two">
        <SectionCard title="About you" eyebrow="User description">
          <div className="field">
            <label className="label" htmlFor="profile-primary-role">
              Primary role
            </label>
            <input
              id="profile-primary-role"
              className="input"
              value={form.primary_role}
              onChange={(event) => setForm({ ...form, primary_role: event.target.value })}
              placeholder="Frontend Engineer"
            />
          </div>
          <div className="field">
            <label className="label" htmlFor="profile-experience">
              Experience level
            </label>
            <input
              id="profile-experience"
              className="input"
              value={form.experience_level}
              onChange={(event) =>
                setForm({ ...form, experience_level: event.target.value })
              }
              placeholder="Intermediate"
            />
          </div>
          <div className="field">
            <label className="label" htmlFor="profile-summary">
              Summary
            </label>
            <textarea
              id="profile-summary"
              className="textarea"
              value={form.summary}
              onChange={(event) => setForm({ ...form, summary: event.target.value })}
              placeholder="Short summary of your focus and context"
            />
          </div>
        </SectionCard>

        <SectionCard title="Skills" eyebrow="List + level (1-5)">
          <div className="grid">
            {skills.map((skill, index) => (
              <div key={`${skill.name}-${index}`} className="grid two">
                <input
                  className="input"
                  value={skill.name}
                  onChange={(event) => updateSkill(index, 'name', event.target.value)}
                  placeholder="Skill name"
                />
                <input
                  className="input"
                  type="number"
                  min="1"
                  max="5"
                  value={skill.level}
                  onChange={(event) => updateSkill(index, 'level', Number(event.target.value))}
                  placeholder="Level"
                />
                <button
                  className="button ghost"
                  type="button"
                  onClick={() => removeSkill(index)}
                >
                  Remove
                </button>
              </div>
            ))}
            <button className="button muted" type="button" onClick={addSkill}>
              Add skill
            </button>
          </div>
        </SectionCard>
      </section>

      <section className="grid two">
        <SectionCard title="Task preferences" eyebrow="Comma separated">
          <div className="field">
            <label className="label" htmlFor="profile-preferred">
              Preferred tasks
            </label>
            <textarea
              id="profile-preferred"
              className="textarea"
              value={form.preferred_tasks}
              onChange={(event) =>
                setForm({ ...form, preferred_tasks: event.target.value })
              }
              placeholder="UI polish, backlog grooming"
            />
          </div>
          <div className="field">
            <label className="label" htmlFor="profile-avoided">
              Avoided tasks
            </label>
            <textarea
              id="profile-avoided"
              className="textarea"
              value={form.avoided_tasks}
              onChange={(event) => setForm({ ...form, avoided_tasks: event.target.value })}
              placeholder="Low-context hotfixes"
            />
          </div>
        </SectionCard>

        <SectionCard title="Availability + notes" eyebrow="Operational">
          <div className="field">
            <label className="label" htmlFor="profile-availability">
              Availability notes
            </label>
            <textarea
              id="profile-availability"
              className="textarea"
              value={form.availability_notes}
              onChange={(event) =>
                setForm({ ...form, availability_notes: event.target.value })
              }
              placeholder="Best hours, time zone, meeting windows"
            />
          </div>
          <div className="field">
            <label className="label" htmlFor="profile-agent-notes">
              Agent notes
            </label>
            <textarea
              id="profile-agent-notes"
              className="textarea"
              value={form.agent_notes}
              onChange={(event) => setForm({ ...form, agent_notes: event.target.value })}
              placeholder="Anything the agents should keep in mind"
            />
          </div>
        </SectionCard>
      </section>

      <div className="inline-actions">
        <button className="button" type="button" onClick={handleSave}>
          Save profile
        </button>
      </div>
    </div>
  );
}
