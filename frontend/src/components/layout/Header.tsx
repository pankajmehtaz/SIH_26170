/**
 * Top header bar showing page title and system status.
 */

import { useEffect, useState } from 'react';
import { healthCheck } from '../../api/client';

interface HeaderProps {
  title?: string;
}

export default function Header({ title }: HeaderProps) {
  const [apiStatus, setApiStatus] = useState<'checking' | 'healthy' | 'error'>('checking');

  useEffect(() => {
    healthCheck()
      .then(() => setApiStatus('healthy'))
      .catch(() => setApiStatus('error'));
  }, []);

  return (
    <header className="app-header">
      <div>
        {title && <h1 style={{ fontSize: '1.1rem', margin: 0 }}>{title}</h1>}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span
          className={`badge ${apiStatus === 'healthy' ? 'badge--normal' : apiStatus === 'error' ? 'badge--critical' : 'badge--info'}`}
          title="Backend API status"
        >
          {apiStatus === 'healthy' ? '● API Connected' : apiStatus === 'error' ? '● API Offline' : '● Checking...'}
        </span>
      </div>
    </header>
  );
}
