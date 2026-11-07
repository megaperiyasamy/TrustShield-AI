import React from 'react';
import {NavLink} from 'react-router-dom';
import {LayoutDashboard, UploadCloud, History as HistoryIcon, LogOut} from 'lucide-react';
import Logo from './Logo';
export default function Sidebar({onLogout}){return <aside className="sidebar"><Logo compact/><nav>
 <NavLink to="/dashboard"><LayoutDashboard/>Dashboard</NavLink>
 <NavLink to="/verify"><UploadCloud/>Upload & Verify</NavLink>
 <NavLink to="/history"><HistoryIcon/>Verification History</NavLink>
 </nav><div className="side-bottom"><small>Smarter Verification.<br/>Safer Tomorrow.</small><button onClick={onLogout}><LogOut/>Logout</button></div></aside>}
