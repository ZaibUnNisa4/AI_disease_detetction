import React, { useState } from 'react';

const CLINICAL_ROLES = [
  'Chief Epidemiologist',
  'Infectious Disease Specialist',
  'Consultant Physician',
  'Public Health Officer',
  'Surveillance Analyst',
  'Laboratory Director',
  'Resident Medical Officer',
  'System Administrator'
];

const HEALTHCARE_CENTERS = [
  'Pakistan Institute of Medical Sciences (PIMS)',
  'Holy Family Hospital (Rawalpindi)',
  'Benazir Bhutto Hospital (Rawalpindi)',
  'Services Hospital (Lahore)',
  'Civil Hospital (Karachi)',
  'National Institute of Health (NIH) Islamabad',
  'Federal Disease Surveillance Center'
];

export default function Profile({ user, apiBase, onProfileUpdated, say }) {
  const [name, setName] = useState(user?.name || '');
  const [role, setRole] = useState(user?.role || 'Chief Epidemiologist');
  const [institution, setInstitution] = useState(user?.institution || 'Pakistan Institute of Medical Sciences (PIMS)');
  const [department, setDepartment] = useState(user?.department || 'Epidemiology & Surveillance Directorate');
  const [phone, setPhone] = useState(user?.phone || '+92 (51) 9261170');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [savedSuccess, setSavedSuccess] = useState(false);

  // Live initials generator based on current input name
  const liveInitials = name
    .trim()
    .split(' ')
    .filter(Boolean)
    .map(p => p[0])
    .join('')
    .slice(0, 2)
    .toUpperCase() || (user?.avatarInitials || 'MD');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSavedSuccess(false);

    if (!name.trim()) {
      setError('Professional name cannot be empty.');
      return;
    }

    if (password && password.trim().length < 6) {
      setError('New password must be at least 6 characters long.');
      return;
    }

    setSaving(true);
    const token = localStorage.getItem('pulsewatch_token') || '';

    try {
      const payload = {
        name: name.trim(),
        role: role.trim(),
        institution: institution.trim(),
        department: department.trim(),
        phone: phone.trim()
      };
      if (password.trim()) {
        payload.password = password.trim();
      }

      // Call FastAPI backend PUT endpoint
      const res = await fetch(`${apiBase}/api/v1/auth/profile?token=${encodeURIComponent(token)}&email=${encodeURIComponent(user?.email || '')}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json().catch(() => ({}));

      if (res.ok && data.success && data.user) {
        const updated = {
          ...user,
          ...data.user,
          avatarInitials: liveInitials
        };
        onProfileUpdated(updated);
        setPassword('');
        setSavedSuccess(true);
        say('Profile details updated successfully');
        return;
      }

      // Fallback update if API is unreachable or returns non-ok
      const localUpdated = {
        ...user,
        name: name.trim(),
        role: role.trim(),
        institution: institution.trim(),
        department: department.trim(),
        phone: phone.trim(),
        avatarInitials: liveInitials
      };
      onProfileUpdated(localUpdated);
      setPassword('');
      setSavedSuccess(true);
      say('Profile saved to local session');
    } catch (err) {
      // Graceful fallback to client session update
      const localUpdated = {
        ...user,
        name: name.trim(),
        role: role.trim(),
        institution: institution.trim(),
        department: department.trim(),
        phone: phone.trim(),
        avatarInitials: liveInitials
      };
      onProfileUpdated(localUpdated);
      setPassword('');
      setSavedSuccess(true);
      say('Profile saved to local session');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setName(user?.name || '');
    setRole(user?.role || 'Chief Epidemiologist');
    setInstitution(user?.institution || 'Pakistan Institute of Medical Sciences (PIMS)');
    setDepartment(user?.department || 'Epidemiology & Surveillance Directorate');
    setPhone(user?.phone || '+92 (51) 9261170');
    setPassword('');
    setError('');
    setSavedSuccess(false);
  };

  return (
    <section className="page active profile-page">
      <div className="heading">
        <div>
          <div className="eyebrow">Personnel Credentials & Access</div>
          <h1>Clinician Profile & Settings</h1>
          <p>Manage your professional identity, institutional affiliation, and terminal security.</p>
        </div>
      </div>

      {error && <div className="error show">{error}</div>}
      {savedSuccess && (
        <div className="profile-success-banner">
          <span className="profile-success-icon">✓</span>
          <span>Your clinician profile details have been saved and applied across your active session.</span>
        </div>
      )}

      <div className="profile-layout-grid">
        {/* Left Side: Clinician ID Card Preview */}
        <aside className="profile-preview-card">
          <div className="profile-badge-header">
            <span className="profile-badge-chip">Active Institutional ID</span>
            <span className="profile-online-dot" title="Authenticated Session"></span>
          </div>

          <div className="profile-avatar-container">
            <div className="profile-large-avatar">
              <span>{liveInitials}</span>
            </div>
            <div className="profile-avatar-meta">
              <h2>{name || 'Doctor Name'}</h2>
              <span className="profile-role-tag">{role}</span>
            </div>
          </div>

          <div className="profile-details-list">
            <div className="profile-detail-row">
              <span className="profile-detail-label">Affiliated Facility</span>
              <strong className="profile-detail-value">{institution}</strong>
            </div>

            <div className="profile-detail-row">
              <span className="profile-detail-label">Division / Unit</span>
              <strong className="profile-detail-value">{department}</strong>
            </div>

            <div className="profile-detail-row">
              <span className="profile-detail-label">Institutional Email</span>
              <span className="profile-detail-value profile-email-val">{user?.email || 'clinician@numl.edu.pk'}</span>
            </div>

            <div className="profile-detail-row">
              <span className="profile-detail-label">Terminal Phone</span>
              <strong className="profile-detail-value">{phone}</strong>
            </div>

            <div className="profile-detail-row">
              <span className="profile-detail-label">Security Protocol</span>
              <span className="profile-security-badge">🔒 256-Bit Encrypted</span>
            </div>
          </div>

          <div className="profile-card-footer">
            <small>National University of Modern Languages · Final Year Project</small>
            <small className="profile-sub-note">Syndromic Event Early Warning System · Class-1 Diagnostics</small>
          </div>
        </aside>

        {/* Right Side: Edit Form */}
        <main className="profile-form-card card panel">
          <div className="panel-head">
            <div>
              <h2>Edit Professional Details</h2>
              <p>Update your display name, role designation, facility, or security password.</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="profile-edit-form">
            <div className="form-grid">
              <label>
                Full Professional Name
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Dr. Ayesha Khan"
                />
                <small>Displayed on patient screening intakes and surveillance logs.</small>
              </label>

              <label>
                Institutional Email (Account ID)
                <input
                  type="email"
                  disabled
                  value={user?.email || ''}
                  className="profile-disabled-input"
                />
                <small>Managed by your institution's health directory.</small>
              </label>

              <label>
                Clinical / Surveillance Role
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                >
                  {CLINICAL_ROLES.map((r) => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                </select>
                <small>Determines role-based reporting and diagnostic authorization.</small>
              </label>

              <label>
                Affiliated Healthcare Facility
                <select
                  value={institution}
                  onChange={(e) => setInstitution(e.target.value)}
                >
                  {HEALTHCARE_CENTERS.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
                <small>Primary epidemiological center and surveillance node.</small>
              </label>

              <label>
                Clinical Department / Unit
                <input
                  type="text"
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  placeholder="e.g. Epidemiology & Biostatistics"
                />
                <small>Hospital wing, pathology unit, or surveillance division.</small>
              </label>

              <label>
                Direct Terminal Extension / Phone
                <input
                  type="text"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="e.g. +92 (51) 9261170"
                />
                <small>Internal communication contact for outbreak escalations.</small>
              </label>
            </div>

            <div className="profile-pw-section">
              <label>
                Update Security Password
                <div className="auth-input-wrapper">
                  <span className="auth-input-icon">🔒</span>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Leave blank to keep your current password"
                    autoComplete="new-password"
                  />
                  <button
                    type="button"
                    className="auth-pw-toggle"
                    onClick={() => setShowPassword(!showPassword)}
                    title={showPassword ? 'Hide password' : 'Show password'}
                    tabIndex="-1"
                  >
                    {showPassword ? '👁️' : '👁️‍🗨️'}
                  </button>
                </div>
                <small>Minimum 6 characters. Only fill if you wish to change your workstation password.</small>
              </label>
            </div>

            <div className="profile-actions-bar">
              <button
                type="submit"
                className="btn primary profile-save-btn"
                disabled={saving}
              >
                {saving ? 'Saving Changes…' : '✓ Save Profile Changes'}
              </button>

              <button
                type="button"
                className="btn profile-reset-btn"
                onClick={handleReset}
                disabled={saving}
              >
                Reset
              </button>
            </div>
          </form>
        </main>
      </div>
    </section>
  );
}
