import React from 'react';
import {Bell} from 'lucide-react';
export default function Topbar({user}){return <header className="topbar"><div/><div className="top-actions"><Bell/><span className="avatar">{user?.name?.[0]?.toUpperCase()||'U'}</span><span>{user?.name||'User'}</span></div></header>}
