import React, {useEffect, useState} from 'react';
import {Routes, Route, Navigate, useNavigate} from 'react-router-dom';
import {auth} from './services/api';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Verify from './pages/Verify';
import Result from './pages/Result';
import History from './pages/History';
import ResetPassword from './pages/ResetPassword';
import ForgotPassword from './pages/ForgotPassword';

export default function App(){
 const [user,setUser]=useState(null);
 const [loading,setLoading]=useState(true);
 useEffect(()=>{ if(localStorage.getItem('trustshield_token')) auth.me().then(setUser).catch(()=>localStorage.removeItem('trustshield_token')).finally(()=>setLoading(false)); else setLoading(false)},[]);
 useEffect(()=>{const h=()=>setUser(null);window.addEventListener('trustshield:unauthorized',h);return()=>window.removeEventListener('trustshield:unauthorized',h)},[]);
 const finish=(data)=>{localStorage.setItem('trustshield_token',data.access_token);setUser(data.user)};
 const logout=()=>{localStorage.removeItem('trustshield_token');setUser(null)};
 if(loading) return <div className="loading-screen"><div className="spinner"/>Loading TrustShield...</div>;
 return <Routes>
   <Route path="/forgot-password" element={<ForgotPassword/>}/>
   <Route path="/reset-password" element={<ResetPassword/>}/>
   <Route path="/login" element={user?<Navigate to="/dashboard"/>:<Login onAuth={finish}/>}/>
   <Route path="/register" element={user?<Navigate to="/dashboard"/>:<Register onAuth={finish}/>}/>
   <Route path="/dashboard" element={user?<Dashboard user={user} onLogout={logout}/>:<Navigate to="/login"/>}/>
   <Route path="/verify" element={user?<Verify onLogout={logout}/>:<Navigate to="/login"/>}/>
   <Route path="/result/:id" element={user?<Result onLogout={logout}/>:<Navigate to="/login"/>}/>
   <Route path="/history" element={user?<History onLogout={logout}/>:<Navigate to="/login"/>}/>
   <Route path="*" element={<Navigate to={user?'/dashboard':'/login'}/>}/>
 </Routes>
}
