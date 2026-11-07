import React from 'react';
export default function Logo({compact=false}){return <div className={'brand '+(compact?'compact':'')}><div className="logo-mark">TS</div><div><b>AI TRUSTSHIELD</b>{!compact&&<span>Intelligent Trust & Risk Detection</span>}</div></div>}
