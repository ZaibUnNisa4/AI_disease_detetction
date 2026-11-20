import { useCallback, useEffect, useMemo, useState } from 'react';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip } from 'chart.js';
import Login from './Login.jsx';
import Profile from './Profile.jsx';
import DiseaseMap from './DiseaseMap.jsx';



ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip);
const API = (localStorage.getItem('pulsewatch-api') || 'http://127.0.0.1:8000').replace(/\/$/, '');
const fmt = n => Number(n || 0).toLocaleString();
const esc = s => String(s ?? '—');
const risk = s => String(s || '').toLowerCase() === 'critical' ? 'critical' : String(s || '').toLowerCase() === 'alert' ? 'alert' : 'normal';
const date = s => !s ? '—' : new Intl.DateTimeFormat('en', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(s));
const month = s => !s ? '—' : new Intl.DateTimeFormat('en', { month: 'short', year: 'numeric' }).format(new Date(`${s}T00:00:00`));

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, { ...options, headers: { 'Content-Type': 'application/json', ...options.headers } });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
  return data;
}

function Badge({ children, kind = '' }) { return <span className={`badge ${kind}`}>{children || 'Unknown'}</span>; }
function ForecastChart({ summary, tall = false }) {
  const labels = (summary?.dengue || []).map(x => month(x.Date));
  const data = {
    labels, datasets: [
      { label: 'Dengue', data: (summary?.dengue || []).map(x => x.Predicted_Cases), borderColor: '#1d7862', backgroundColor: 'rgba(29,120,98,.08)', pointBackgroundColor: '#1d7862', pointRadius: 3, borderWidth: 2.5, tension: .35, fill: true },
      { label: 'Typhoid', data: (summary?.typhoid || []).map(x => x.Predicted_Cases), borderColor: '#dfa45b', pointBackgroundColor: '#dfa45b', pointRadius: 3, borderWidth: 2.5, tension: .35 }
    ]
  };
  const options = { maintainAspectRatio: false, responsive: true, interaction: { mode: 'index', intersect: false }, plugins: { legend: { display: false }, tooltip: { backgroundColor: '#173a34', callbacks: { afterBody(items) { const list = items[0]?.dataset.label === 'Dengue' ? summary?.dengue : summary?.typhoid; const row = list?.[items[0]?.dataIndex]; return row ? `Risk: ${row.Risk_Level} · Z ${Number(row.Z_Score).toFixed(2)}` : ''; } } } }, scales: { x: { grid: { display: false }, ticks: { color: '#899590', font: { size: 10 } } }, y: { beginAtZero: true, grid: { color: '#eef1ed' }, border: { display: false }, ticks: { color: '#899590', font: { size: 10 }, callback: v => Number(v).toLocaleString() } } } };
  return <div className={`chart ${tall ? 'tall' : ''}`}><Line data={data} options={options} /></div>;
}
function PatientRows({ rows, compact = false }) {
  if (!rows?.length) return <tr><td colSpan={compact ? 6 : 8} className="empty">No patient records returned.</td></tr>;
  return rows.map((p, i) => <tr key={p.id || p.patient_code || i}>{compact ? <><td><span className="patient"><span className="patient-icon">♙</span>{esc(p.patient_code || p.id)}</span></td><td>{esc(p.age)} / {esc(p.gender)}</td><td>{esc(p.fever_duration_days)} days</td><td><Badge kind={p.predicted_disease === 'Typhoid' ? 'typhoid' : ''}>{p.predicted_disease}</Badge></td><td>{p.confidence_score == null ? '—' : `${Math.round(Number(p.confidence_score) * 100)}%`}</td><td>{date(p.created_at)}</td></> : <><td>{esc(p.patient_code || p.id)}</td><td>{esc(p.age)}</td><td>{esc(p.gender)}</td><td>{esc(p.fever_duration_days)} days</td><td>{p.skin_manifestation ? 'Present' : 'None'}</td><td><Badge kind={p.predicted_disease === 'Typhoid' ? 'typhoid' : ''}>{p.predicted_disease}</Badge></td><td>{p.confidence_score == null ? '—' : `${Math.round(Number(p.confidence_score) * 100)}%`}</td><td>{date(p.created_at)}</td></>}</tr>);
}

export default function App() {
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('pulsewatch_user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [page, setPage] = useState('dashboard');
  const [summary, setSummary] = useState(null);
  const [patients, setPatients] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [health, setHealth] = useState(null);
  const [error, setError] = useState('');
  const [horizon, setHorizon] = useState(6);
  const [search, setSearch] = useState('');
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [notice, setNotice] = useState('');
  const [menuOpen, setMenuOpen] = useState(false);
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const [screeningLocation, setScreeningLocation] = useState(null);
  const say = message => { setNotice(message); window.setTimeout(() => setNotice(''), 2600); };

  const handleLoginSuccess = (userData, token) => {
    setUser(userData);
    try {
      localStorage.setItem('pulsewatch_user', JSON.stringify(userData));
      if (token) localStorage.setItem('pulsewatch_token', token);
    } catch (e) { }
    say(`Authenticated: ${userData.name || 'Doctor'}`);
  };

  const handleProfileUpdated = (updatedUser) => {
    setUser(updatedUser);
    try {
      localStorage.setItem('pulsewatch_user', JSON.stringify(updatedUser));
    } catch (e) { }
  };

  const handleLogout = () => {
    const token = localStorage.getItem('pulsewatch_token');
    if (token) {
      fetch(`${API}/api/v1/auth/logout?token=${encodeURIComponent(token)}`, { method: 'POST' }).catch(() => { });
    }
    setUser(null);
    setProfileMenuOpen(false);
    try {
      localStorage.removeItem('pulsewatch_user');
      localStorage.removeItem('pulsewatch_token');
    } catch (e) { }
    say('Workstation session logged out');
  };

  const loadDashboard = useCallback(async () => {
    setError('');
    const results = await Promise.allSettled([
      request('/api/v1/health'),
      request('/api/v1/surveillance/summary?months=6'),
      request('/api/v1/patients/recent?limit=50'),
      request('/api/v1/alerts?limit=50')
    ]);
    const errors = [];
    if (results[0].status === 'fulfilled') setHealth(results[0].value); else errors.push('API health check failed');
    if (results[1].status === 'fulfilled') setSummary(results[1].value); else errors.push('Forecast unavailable');
    if (results[2].status === 'fulfilled') setPatients(results[2].value.patients || []); else errors.push('Patient records unavailable');
    if (results[3].status === 'fulfilled') setAlerts(results[3].value.alerts || []); else errors.push('Database alerts unavailable');
    if (errors.length) setError(`${errors.join(' · ')}. Check that the API is running at ${API}.`);
  }, []);

  const loadPatients = useCallback(async () => { try { const data = await request('/api/v1/patients/recent?limit=50'); setPatients(data.patients || []); } catch (e) { setError(e.message); } }, []);
  const loadAlerts = useCallback(async () => { try { const data = await request('/api/v1/alerts?limit=50'); setAlerts(data.alerts || []); } catch (e) { setError(e.message); } }, []);
  const loadForecast = useCallback(async () => { setBusy(true); try { setSummary(await request(`/api/v1/surveillance/summary?months=${horizon}`)); say('Forecast updated'); } catch (e) { setError(e.message); } finally { setBusy(false); } }, [horizon]);

  useEffect(() => {
    if (user) loadDashboard();
  }, [user, loadDashboard]);

  useEffect(() => {
    if (!user) return;
    if (page === 'patients') loadPatients();
    if (page === 'alerts') loadAlerts();
  }, [user, page, loadPatients, loadAlerts]);

  const forecastRows = useMemo(() => [...(summary?.dengue || []), ...(summary?.typhoid || [])].sort((a, b) => String(a.Date).localeCompare(String(b.Date))), [summary]);
  const riskAlerts = summary?.active_outbreak_alerts || [];
  const worst = riskAlerts.find(a => risk(a.Risk_Level) === 'critical') || riskAlerts[0];
  const visiblePatients = patients.filter(p => String(p.patient_code || '').toLowerCase().includes(search.toLowerCase()));
  const go = target => { setPage(target); setMenuOpen(false); setProfileMenuOpen(false); if (target === 'surveillance' && !summary) loadForecast(); };

  async function submitScreening(event) {
    event.preventDefault(); setBusy(true); setResult(null);
    const form = new FormData(event.currentTarget);
    const payload = { patient_code: form.get('patient_code'), age: Number(form.get('age')), gender: form.get('gender'), fever_duration_days: Number(form.get('fever_duration_days')), skin_manifestation: form.get('skin_manifestation') === 'true', save_to_db: form.get('save_to_db') === 'on' };
    try { const data = await request('/api/v1/patient/screen', { method: 'POST', body: JSON.stringify(payload) }); setResult(data); say('Screening complete'); if (data.db_logged) loadDashboard(); }
    catch (e) { setResult({ error: e.message }); } finally { setBusy(false); }
  }

  // If user is not authenticated, render the dedicated Login Portal
  if (!user) {
    return (
      <>
        <Login apiBase={API} onLoginSuccess={handleLoginSuccess} />
        <div className={`notice ${notice ? 'show' : ''}`}>{notice}</div>
      </>
    );
  }

  const userInitials = user.avatarInitials || (user.name ? user.name.split(' ').filter(Boolean).map(n => n[0]).join('').slice(0, 2).toUpperCase() : 'MD');

  return <div className="shell">
    <aside className={`sidebar ${menuOpen ? 'open' : ''}`}>
      <div className="brand"><span className="mark">✳</span><span>Syndromic Event<small>EARLY WARNING SYSTEM</small></span></div>
      <div className="nav-label">Workspace</div>
      <nav className="nav">
        {[
          ['dashboard', '◫', 'Overview'],
          ['map', '⌖', 'Disease map'],
          ['screening', '⊙', 'Patient screening'],
          ['surveillance', '⌁', 'Surveillance'],
          ['patients', '♙', 'Patient records'],
          ['alerts', '♢', 'Alert centre'],
          ['profile', '⚙', 'Profile & Settings']
        ].map(([id, icon, label]) => (
          <button key={id} className={page === id ? 'active' : ''} onClick={() => go(id)}>{icon}<span>{label}</span></button>
        ))}
      </nav>
      <div className="side-bottom">
        <div className="side-user-card">
          <div className="side-user-main" onClick={() => go('profile')} title="View Clinician Profile">
            <span className="side-user-avatar">{userInitials}</span>
            <div className="side-user-text">
              <strong>{user.name}</strong>
              <small>{user.role || 'Clinical Staff'}</small>
            </div>
          </div>
          <div className="side-user-btn-row">
            <button className="side-profile-btn" onClick={() => go('profile')} title="Edit Profile Details">
              <span>⚙ Edit Profile</span>
            </button>
            <button className="side-logout-btn" onClick={handleLogout} title="Sign Out">
              <span>⎋ Sign Out</span>
            </button>
          </div>
        </div>
        <div className="api-pill"><i className={`dot ${health?.status === 'healthy' ? 'ok' : ''}`}></i><span>{health ? health.status === 'healthy' ? 'API connected' : 'API degraded' : 'Checking API…'}</span></div>
        <small>Dengue & typhoid monitoring<br />NUML · Final Year Project</small>
      </div>
    </aside>

    <main className="main">
      <header className="topbar">
        <div className="mobile-brand"><button onClick={() => setMenuOpen(!menuOpen)}>☰</button><span className="mark">✳</span>Syndromic Event Early Warning System</div>
        <div className="crumb">Workspace / <b id="crumbTitle">{{ dashboard: 'Overview', map: 'Disease map', screening: 'Patient screening', surveillance: 'Surveillance', patients: 'Patient records', alerts: 'Alert centre', profile: 'Profile & Settings' }[page]}</b></div>
        <div className="top-actions">
          <span className="top-date">{new Intl.DateTimeFormat('en', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' }).format(new Date())}</span>

          {/* Interactive Profile Capsule & Dropdown Menu */}
          <div className="top-user-menu-wrapper">
            <button
              type="button"
              className={`top-user-capsule-btn ${profileMenuOpen ? 'active' : ''}`}
              onClick={() => setProfileMenuOpen(!profileMenuOpen)}
              title="Click to open Clinician Profile Menu"
            >
              <span className="avatar user-badge-avatar">{userInitials}</span>
              <div className="top-user-info">
                <span className="top-user-name">{user.name}</span>
                <span className="top-user-role">{user.role || 'Staff'}</span>
              </div>
              <span className="top-menu-caret">{profileMenuOpen ? '▴' : '▾'}</span>
            </button>

            {profileMenuOpen && (
              <div className="top-profile-dropdown card">
                <div className="dropdown-user-header">
                  <div className="dropdown-avatar">{userInitials}</div>
                  <div className="dropdown-user-meta">
                    <strong>{user.name}</strong>
                    <small>{user.email}</small>
                    <span className="dropdown-role-chip">{user.role || 'Clinical Staff'}</span>
                  </div>
                </div>
                <div className="dropdown-divider"></div>
                <div className="dropdown-facility-row">
                  <small>Healthcare Facility:</small>
                  <span>{user.institution || 'National Surveillance Network'}</span>
                </div>
                <div className="dropdown-divider"></div>
                <button
                  type="button"
                  className="dropdown-menu-item"
                  onClick={() => { setProfileMenuOpen(false); go('profile'); }}
                >
                  <span className="dropdown-item-icon">⚙</span>
                  <span>Edit Profile Details</span>
                </button>
                <button
                  type="button"
                  className="dropdown-menu-item signout"
                  onClick={() => { setProfileMenuOpen(false); handleLogout(); }}
                >
                  <span className="dropdown-item-icon">⎋</span>
                  <span>Sign Out</span>
                </button>
              </div>
            )}
          </div>

          <button className="top-signout-btn" onClick={handleLogout} title="Sign out of this terminal session">
            <span className="signout-glyph">⎋</span>
            <span>Sign Out</span>
          </button>
        </div>
      </header>

      {error && <div className="error show">{error}</div>}

      {page === 'dashboard' && <section className="page active">
        <div className="heading">
          <div>
            <div className="eyebrow">Public health intelligence</div>
            <h1>Good morning, {user.name?.split(' ')[0] || 'Doctor'}</h1>
            <p>Welcome to Syndromic Event Early Warning System · Connected to {user.institution || 'NUML Surveillance Network'}</p>
          </div>
          <button className="btn" onClick={() => { loadDashboard(); say('Dashboard refreshed'); }}>↻ &nbsp;Refresh data</button>
        </div>
        <div className="metrics">
          <article className="card metric"><div>Screenings logged <i>♙</i></div><strong>{fmt(patients.length)}</strong><small>Recent records available</small></article>
          <article className="card metric"><div>Dengue forecast <i>⌁</i></div><strong>{fmt(summary?.dengue?.[0]?.Predicted_Cases)}</strong><small>Next month · projected cases</small></article>
          <article className="card metric"><div>Typhoid forecast <i>⌁</i></div><strong>{fmt(summary?.typhoid?.[0]?.Predicted_Cases)}</strong><small>Next month · projected cases</small></article>
          <article className="card metric"><div>Active alerts <i className="amber">♢</i></div><strong>{riskAlerts.length}</strong><small>{riskAlerts.length ? 'Elevated-risk forecast periods' : 'No forecast risk periods'}</small></article>
        </div>
        <div className="grid">
          <article className="card panel"><div className="panel-head"><div><h2>Six-month outlook</h2><p>Projected cases across both diseases</p></div><div className="legend"><span><i className="key" />Dengue</span><span><i className="key ty" />Typhoid</span></div></div>{summary ? <ForecastChart summary={summary} /> : <div className="empty">Loading forecast…</div>}</article>
          <article className="card panel"><div className="panel-head"><div><h2>Risk overview</h2><p>Model-assessed upcoming periods</p></div><button className="btn small" onClick={() => go('alerts')}>View all</button></div><div className={`alert-summary ${worst ? risk(worst.Risk_Level) : ''}`}><span className="alert-icon">{worst ? '♢' : '✓'}</span><div><div className="alert-title">{worst ? `${worst.Risk_Level} risk detected` : 'No elevated risk detected'}</div><div className="alert-copy">{worst ? `${worst.Disease} · ${month(worst.Date)} · Z-score ${Number(worst.Z_Score).toFixed(2)}` : 'All periods below the alert threshold.'}</div></div><span className="alert-count">{riskAlerts.length}</span></div>{riskAlerts.slice(0, 3).map((a, i) => <div className="alert-row" key={i}><i className={`severity ${risk(a.Risk_Level)}`} /><div><strong>{a.Disease} · {a.Risk_Level} risk</strong><small>{month(a.Date)} · {fmt(a.Predicted_Cases)} projected cases</small></div><time>Z {Number(a.Z_Score).toFixed(2)}</time></div>)}{!riskAlerts.length && <div className="empty">No upcoming forecast alerts.</div>}</article>
        </div>

        {/* Geospatial Outbreak & Endemicity Map Dashboard Preview Widget */}
        <div className="card dashboard-map-preview-card">
          <div className="preview-head">
            <div>
              <h2>National Geospatial Outbreak & Endemicity Map</h2>
              <p>Live district-level transmission vectors across Pakistan · Rawalpindi Dengue Epicenter & Karachi Typhoid XDR Hotspot</p>
            </div>
            <button className="btn small" onClick={() => go('map')}>Open Interactive Map →</button>
          </div>
          <div className="preview-content">
            <div className="preview-hotspots-list">
              <div className="preview-hotspot-item" onClick={() => go('map')}>
                <span className="hotspot-avatar dengue">🦟</span>
                <div className="hotspot-info">
                  <strong>Rawalpindi · Dengue Outbreak</strong>
                  <small>432 cases · Z 3.18 · Aedes aegypti DENV-2</small>
                </div>
              </div>
              <div className="preview-hotspot-item" onClick={() => go('map')}>
                <span className="hotspot-avatar typhoid">🧫</span>
                <div className="hotspot-info">
                  <strong>Karachi · Typhoid XDR Cluster</strong>
                  <small>785 cases · Z 3.25 · Salmonella Typhi H58</small>
                </div>
              </div>
              <div className="preview-hotspot-item" onClick={() => go('map')}>
                <span className="hotspot-avatar typhoid">🧫</span>
                <div className="hotspot-info">
                  <strong>Hyderabad · Resistant Typhoid</strong>
                  <small>275 cases · Z 3.06 · Waterborne Warning</small>
                </div>
              </div>
              <div className="preview-hotspot-item" onClick={() => go('map')}>
                <span className="hotspot-avatar dengue">🦟</span>
                <div className="hotspot-info">
                  <strong>Lahore · Dual Surveillance</strong>
                  <small>310 cases · Z 2.42 · Mixed Transmission</small>
                </div>
              </div>
            </div>
            <div className="preview-cta-box">
              <div>
                <h3>Interactive Geospatial Surveillance</h3>
                <p>Explore geographic infection clusters, vector entomology, and sentinel triage hospitals across 20 monitored districts.</p>
              </div>
              <button className="btn preview-btn" onClick={() => go('map')}>Launch Outbreak Map ⌖</button>
            </div>
          </div>
        </div>

        <div className="grid lower">
          <article className="card panel"><div className="panel-head"><div><h2>Recent screenings</h2><p>Latest records from your database</p></div><button className="btn small" onClick={() => go('patients')}>All records →</button></div><div className="table-wrap"><table><thead><tr><th>Patient</th><th>Age / Gender</th><th>Fever</th><th>Result</th><th>Confidence</th><th>Date</th></tr></thead><tbody><PatientRows rows={patients.slice(0, 8)} compact /></tbody></table></div></article>
          <article className="card panel"><div className="panel-head"><div><h2>System status</h2><p>Inference services</p></div></div>{health && [['Dengue forecasting', 'Holt–Winters', health.dengue_model], ['Typhoid forecasting', 'SARIMA', health.typhoid_model], ['Patient identification', 'SVM classifier', health.identification_svm], ['Database', 'Supabase', health.supabase_database]].map(([n, t, s]) => <div className="model-row" key={n}><div><div className="model-name">{n}</div><div className="model-type">{t}</div></div><span className="online"><i /> {String(s).toLowerCase().includes('offline') ? 'Issue' : 'Online'}</span></div>)}</article>
        </div>
        <div className="footnote">Forecasts support surveillance planning. Screening results are not a substitute for professional medical diagnosis.</div>
      </section>}

      {page === 'screening' && <section className="page active"><div className="heading"><div><div className="eyebrow">Clinical intake</div><h1>Patient screening</h1><p>Receive a model-based screening and community context.</p></div></div>
        {screeningLocation && (
          <div className="prefill-notice">
            <span>
              📍 Active Surveillance Location: <b>{screeningLocation.name} ({screeningLocation.province})</b> ·
              High <b>{screeningLocation.primary_disease}</b> Endemicity District ({screeningLocation.projected_cases} projected cases)
            </span>
            <button type="button" onClick={() => setScreeningLocation(null)} title="Clear location">✕</button>
          </div>
        )}
        <div className="grid screen-grid"><form className="card panel" onSubmit={submitScreening}><div className="panel-head"><div><h2>Patient details</h2><p>All fields are required</p></div></div><div className="form-grid"><label>Patient code<input name="patient_code" placeholder="e.g. PAT-001" defaultValue={screeningLocation ? `PAT-${screeningLocation.name.slice(0, 3).toUpperCase()}-` : ''} required maxLength="40" /><small>Use a local identifier; avoid full names.</small></label><label>Age<input name="age" type="number" min="0" max="120" placeholder="Years" required /></label><label>Gender<select name="gender" required defaultValue=""><option value="" disabled>Select gender</option><option>Male</option><option>Female</option><option>Other</option></select></label><label>Fever duration<input name="fever_duration_days" type="number" min="1" max="120" placeholder="Days" required /></label><label>Skin manifestation<select name="skin_manifestation" required defaultValue=""><option value="" disabled>Select an option</option><option value="true">Present</option><option value="false">Not present</option></select></label></div><label className="save-row"><span>Save screening to patient records<small>Store this consultation in the connected database.</small></span><input type="checkbox" name="save_to_db" defaultChecked /></label><button className="btn primary" disabled={busy}>{busy ? 'Screening…' : 'Run screening →'}</button></form><article className="card panel result-card"><div className="panel-head"><div><h2>Screening result</h2><p>Clinical model output</p></div></div>{!result ? <div className="empty">Complete the intake form to see the prediction, confidence, and current community risk context.</div> : result.error ? <div className="empty">Screening failed: {result.error}</div> : <><Badge kind={result.predicted_disease === 'Typhoid' ? 'typhoid' : ''}>Model prediction</Badge><h2 style={{ fontSize: 23, margin: '14px 0 5px' }}>{result.predicted_disease}</h2><div className="model-type">{result.confidence_percentage} model confidence</div><div className="model-row"><span>Dengue likelihood</span><b>{Math.round((result.probabilities?.Dengue || 0) * 100)}%</b></div><div className="model-row"><span>Typhoid likelihood</span><b>{Math.round((result.probabilities?.Typhoid || 0) * 100)}%</b></div><div className="alert-summary"><div className="alert-copy"><b>Community context · {result.community_context?.disease}</b><br />Current status: {result.community_context?.current_outbreak_risk} · Z-score {Number(result.community_context?.current_z_score || 0).toFixed(2)}<br />{result.db_logged ? 'Saved to patient records.' : 'Database save not confirmed.'}</div></div></>}<div className="footnote">This tool supports clinical review and does not diagnose disease.</div></article></div></section>}

      {page === 'surveillance' && <section className="page active"><div className="heading"><div><div className="eyebrow">Forecasting & anomaly detection</div><h1>Surveillance</h1><p>Monthly projections compared with historical baselines.</p></div><div className="toolbar"><select value={horizon} onChange={e => setHorizon(Number(e.target.value))}><option value="3">Next 3 months</option><option value="6">Next 6 months</option><option value="12">Next 12 months</option></select><button className="btn" onClick={loadForecast} disabled={busy}>↻ Update</button></div></div><article className="card panel"><div className="panel-head"><div><h2>Disease forecast</h2><p>Hover over points for projected counts and risk levels.</p></div></div>{summary && <ForecastChart summary={summary} tall />}</article><div className="grid lower"><article className="card panel"><div className="panel-head"><div><h2>Forecast schedule</h2><p>Monthly projection and risk score</p></div></div><div className="table-wrap"><table><thead><tr><th>Month</th><th>Disease</th><th>Cases</th><th>Baseline</th><th>Z-score</th><th>Risk</th></tr></thead><tbody>{forecastRows.map((r, i) => <tr key={i}><td>{month(r.Date)}</td><td><Badge kind={r.Disease === 'Typhoid' ? 'typhoid' : ''}>{r.Disease}</Badge></td><td>{fmt(r.Predicted_Cases)}</td><td>{fmt(r.Baseline_Mean)}</td><td>{Number(r.Z_Score).toFixed(2)}</td><td><Badge kind={risk(r.Risk_Level)}>{r.Risk_Level}</Badge></td></tr>)}</tbody></table></div></article><article className="card panel"><div className="panel-head"><div><h2>Historical baselines</h2><p>Computed from surveillance records</p></div></div>{['Dengue', 'Typhoid'].map(k => { const b = summary?.baselines?.[k] || {}; return <div className="model-row" key={k}><div><div className="model-name">{k}</div><div className="model-type">{fmt(b.total_months)} historical months</div></div><div className="model-name">{fmt(Math.round(b.mean || 0))} / month</div></div> })}<div className="footnote">Alert: Z-score ≥ 2. Critical: Z-score ≥ 3.</div></article></div></section>}

      {page === 'patients' && <section className="page active"><div className="heading"><div><div className="eyebrow">Consultation history</div><h1>Patient records</h1><p>Recently saved screening records from Supabase.</p></div><div className="toolbar"><input className="search" placeholder="⌕ Search patient code…" value={search} onChange={e => setSearch(e.target.value)} /><button className="btn" onClick={loadPatients}>↻ Refresh</button></div></div><article className="card panel"><div className="table-wrap"><table><thead><tr><th>Patient code</th><th>Age</th><th>Gender</th><th>Fever</th><th>Skin signs</th><th>Result</th><th>Confidence</th><th>Recorded</th></tr></thead><tbody><PatientRows rows={visiblePatients} /></tbody></table></div></article><div className="footnote">Patient records contain sensitive health information. Follow your institution’s data handling policy.</div></section>}

      {page === 'alerts' && <section className="page active"><div className="heading"><div><div className="eyebrow">Risk monitoring</div><h1>Alert centre</h1><p>Potential elevated-risk periods for public health review.</p></div><button className="btn" onClick={loadAlerts}>↻ Refresh</button></div><div className="card panel alert-list">{alerts.length ? alerts.map((a, i) => <div className="alert-row" key={a.id || i}><i className={`severity ${risk(a.risk_level)}`} /><div style={{ flex: 1 }}><strong>{a.disease} · {a.risk_level}</strong><small>{a.alert_message || a.region || 'Elevated risk recorded'} · {date(a.created_at || a.forecast_month)}</small></div><time>Z {Number(a.z_score || 0).toFixed(2)}</time></div>) : <div className="empty">No alerts are currently available.</div>}</div><div className="footnote">Forecast alerts are statistical signals. Verify through local public health reporting channels.</div></section>}

      {page === 'map' && <section className="page active">
        <DiseaseMap
          apiBase={API}
          onSelectForScreening={(region) => {
            setScreeningLocation(region);
            go('screening');
            say(`District ${region.name} set for clinical intake`);
          }}
          onRequestRefresh={loadDashboard}
        />
      </section>}

      {page === 'profile' && <Profile user={user} apiBase={API} onProfileUpdated={handleProfileUpdated} say={say} />}
    </main>
    <div className={`notice ${notice ? 'show' : ''}`}>{notice}</div>
  </div>;
}


