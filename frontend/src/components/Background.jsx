import React from 'react';
export default function Background(){return <div className="bg-grid"><div className="grid-wave wave1"/><div className="grid-wave wave2"/><div className="particle-field">{Array.from({length:38},(_,i)=><i key={i} style={{'--i':i}}/> )}</div></div>}
