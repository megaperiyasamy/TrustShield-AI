import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, ArrowLeft, ShieldCheck } from 'lucide-react';
import Background from '../components/Background';
import Logo from '../components/Logo';
import { auth } from '../services/api';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [resetUrl, setResetUrl] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const submit = async (e) => {
    e.preventDefault(); setError(''); setMessage(''); setResetUrl(''); setBusy(true);
    try { const result = await auth.forgotPassword({ email }); setMessage(result.message); setResetUrl(result.development_reset_url || ''); }
    catch (e) { setError(e.message); }
    finally { setBusy(false); }
  };
  return <div className="auth-page"><Background/><div className="auth-left"><Logo/><div className="hero-copy"><h1>Recover your<br/>TrustShield account.</h1><p>Request a secure password reset link to regain access to your workspace.</p></div></div><form className="auth-card" onSubmit={submit}><Logo/><div className="welcome"><h2>Forgot password?</h2><p>Enter the email address linked to your account.</p></div>{error&&<div className="error">{error}</div>}{message&&<div className="success-message">{message}</div>}<label>Email<input value={email} onChange={e=>setEmail(e.target.value)} placeholder="you@example.com" type="email" autoComplete="email" required/><Mail/></label><button className="primary-btn" disabled={busy}>{busy?'PREPARING...':'SEND RESET LINK'}</button>{resetUrl&&<div className="reset-dev"><b>Local development link</b><a href={resetUrl}>Open password reset page</a><small>For live email delivery, configure SMTP settings in the backend environment.</small></div>}<p className="auth-switch"><Link to="/login"><ArrowLeft size={15}/> Back to login</Link></p><div className="secure-note"><ShieldCheck size={14}/> Reset links expire after 30 minutes and can be used once.</div></form></div>;
}
