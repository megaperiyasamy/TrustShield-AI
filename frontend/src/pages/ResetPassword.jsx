import React, { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { Lock, ShieldCheck } from 'lucide-react';
import Background from '../components/Background';
import Logo from '../components/Logo';
import { auth } from '../services/api';

export default function ResetPassword() {
  const [params] = useSearchParams();
  const nav = useNavigate();
  const token = params.get('token') || '';
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const submit = async (e) => {
    e.preventDefault(); setError('');
    if (!token) { setError('This reset link is missing its token. Request a new link.'); return; }
    if (password !== confirm) { setError('The passwords do not match.'); return; }
    setBusy(true);
    try { await auth.resetPassword({ token, password }); nav('/login', { replace: true, state: { message: 'Password updated. Please log in with your new password.' } }); }
    catch (e) { setError(e.message); }
    finally { setBusy(false); }
  };
  return <div className="auth-page"><Background/><div className="auth-left"><Logo/><div className="hero-copy"><h1>Set a new<br/>password.</h1><p>Choose a strong password to secure your TrustShield account.</p></div></div><form className="auth-card" onSubmit={submit}><Logo/><div className="welcome"><h2>Reset password</h2><p>Use at least 8 characters.</p></div>{error&&<div className="error">{error}</div>}<label>New password<input value={password} onChange={e=>setPassword(e.target.value)} type="password" autoComplete="new-password" minLength="8" required/><Lock/></label><label>Confirm password<input value={confirm} onChange={e=>setConfirm(e.target.value)} type="password" autoComplete="new-password" minLength="8" required/><Lock/></label><button className="primary-btn" disabled={busy}>{busy?'UPDATING...':'UPDATE PASSWORD'}</button><p className="auth-switch"><Link to="/login">Back to login</Link></p><div className="secure-note"><ShieldCheck size={14}/> Your reset link is single-use and expires after 30 minutes.</div></form></div>;
}
