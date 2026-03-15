import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './Auth.css';

const PARTICLES = ['🧴', '📄', '🔩', '🍃', '♻️', '🌍'];

function getStrength(pw) {
  if (!pw) return { score: 0, label: '', color: 'transparent' };
  let s = 0;
  if (pw.length >= 3) s++;
  if (pw.length >= 6) s++;
  if (/[A-Z]/.test(pw)) s++;
  if (/\d/.test(pw)) s++;
  if (/[^a-zA-Z0-9]/.test(pw)) s++;
  const levels = [
    { label: 'Weak', color: '#ef4444' },
    { label: 'Fair', color: '#f59e0b' },
    { label: 'Good', color: '#10b981' },
    { label: 'Strong', color: '#06d6a0' },
    { label: 'Excellent', color: '#34d399' },
  ];
  const idx = Math.min(s, levels.length) - 1;
  return { score: s, ...(idx >= 0 ? levels[idx] : { label: '', color: 'transparent' }) };
}

export default function Login() {
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [remember, setRemember] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const navigate = useNavigate();

  // clear messages when switching modes
  useEffect(() => { setError(null); setSuccess(null); }, [mode]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);

    const endpoint = mode === 'login' ? '/api/auth/login' : '/api/auth/register';

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (!res.ok) {
        const payload = await res.json().catch(() => null);
        throw new Error((payload && payload.detail) || `${mode === 'login' ? 'Login' : 'Registration'} failed`);
      }

      const payload = await res.json();
      const token = payload.access_token;
      const user = payload.user || null;

      const storage = remember ? localStorage : sessionStorage;
      storage.setItem('token', token);
      if (user) storage.setItem('user', JSON.stringify(user));

      if (mode === 'register') {
        setSuccess('Account created! Redirecting…');
        setTimeout(() => navigate('/profile'), 800);
      } else {
        navigate('/profile');
      }
    } catch (err) {
      if (err.message === 'Failed to fetch' || err.name === 'TypeError') {
        setError('Server unreachable — make sure the backend is running.');
      } else {
        setError(err.message || `${mode === 'login' ? 'Login' : 'Registration'} failed`);
      }
    } finally {
      setLoading(false);
    }
  };

  const pwStrength = mode === 'register' ? getStrength(password) : null;

  return (
    <div className="auth-page">
      {/* ─── Left branding panel ─── */}
      <div className="auth-left">
        <div className="auth-particles">
          {PARTICLES.map((p, i) => <span key={i} className="particle">{p}</span>)}
        </div>
        <div className="brand-logo">♻️</div>
        <div className="brand-name">SmartBin AI</div>
        <p className="brand-tagline">
          Snap a photo, classify waste with AI, earn points, and help save the planet — one item at a time.
        </p>
        <div className="auth-features">
          <div className="feature-pill"><span className="fp-icon">📸</span> AI-powered waste classification</div>
          <div className="feature-pill"><span className="fp-icon">🏆</span> Gamified recycling with leaderboards</div>
          <div className="feature-pill"><span className="fp-icon">🌱</span> Track your environmental impact</div>
        </div>
      </div>

      {/* ─── Right form panel ─── */}
      <div className="auth-right">
        <div className="auth-card">
          {/* Mode toggle */}
          <div className="mode-toggle">
            <button
              type="button"
              className={`mode-btn ${mode === 'login' ? 'active' : ''}`}
              onClick={() => setMode('login')}
            >
              Sign In
            </button>
            <button
              type="button"
              className={`mode-btn ${mode === 'register' ? 'active' : ''}`}
              onClick={() => setMode('register')}
            >
              Sign Up
            </button>
          </div>

          <h2>{mode === 'login' ? 'Welcome back' : 'Create your account'}</h2>
          <p className="auth-subtitle">
            {mode === 'login'
              ? 'Enter your credentials to continue your eco-journey.'
              : 'Join the community and start saving the planet!'}
          </p>

          <form onSubmit={handleSubmit} className="auth-form" autoComplete="off">
            {/* Username */}
            <div className="form-group">
              <label htmlFor="auth-username">Username</label>
              <div className="input-wrapper">
                <span className="input-icon">👤</span>
                <input
                  id="auth-username"
                  autoFocus
                  type="text"
                  placeholder="e.g. eco_warrior"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>
            </div>

            {/* Password */}
            <div className="form-group">
              <label htmlFor="auth-password">Password</label>
              <div className="input-wrapper">
                <span className="input-icon">🔒</span>
                <input
                  id="auth-password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder={mode === 'login' ? '••••••••' : 'Choose a password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  className="toggle-pw"
                  onClick={() => setShowPassword(!showPassword)}
                  tabIndex={-1}
                  aria-label="Toggle password visibility"
                >
                  {showPassword ? '🙈' : '👁️'}
                </button>
              </div>

              {/* strength meter (register only) */}
              {mode === 'register' && password.length > 0 && (
                <>
                  <div className="strength-bar-track">
                    <div
                      className="strength-bar-fill"
                      style={{
                        width: `${(pwStrength.score / 5) * 100}%`,
                        background: pwStrength.color,
                      }}
                    />
                  </div>
                  <span className="strength-label" style={{ color: pwStrength.color }}>
                    {pwStrength.label}
                  </span>
                </>
              )}
            </div>

            {/* Remember me (login only) */}
            {mode === 'login' && (
              <div className="options-row">
                <label className="remember-label">
                  <input
                    type="checkbox"
                    checked={remember}
                    onChange={(e) => setRemember(e.target.checked)}
                  />
                  Remember me
                </label>
              </div>
            )}

            {/* Messages */}
            {error && <div className="auth-error">⚠️ {error}</div>}
            {success && <div className="auth-success">✅ {success}</div>}

            {/* Submit */}
            <button type="submit" className="auth-submit" disabled={loading}>
              {loading ? (
                <span className="spinner" />
              ) : mode === 'login' ? (
                <>🚀 Sign In</>
              ) : (
                <>🎉 Create Account</>
              )}
            </button>
          </form>

          <div className="auth-divider">or</div>
          <p className="auth-subtitle" style={{ textAlign: 'center', marginBottom: 0 }}>
            {mode === 'login'
              ? "Don't have an account? Click Sign Up above!"
              : 'Already a member? Switch to Sign In!'}
          </p>
        </div>
      </div>
    </div>
  );
}