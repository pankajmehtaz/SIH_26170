/**
 * Page shell wrapping content with header + title.
 */

import type { ReactNode } from 'react';
import Header from './Header';

interface PageShellProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
  actions?: ReactNode;
}

export default function PageShell({ title, subtitle, children, actions }: PageShellProps) {
  return (
    <>
      <Header title={title} />
      <main className="app-content">
        <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h2 className="page-title">{title}</h2>
            {subtitle && <p className="page-subtitle">{subtitle}</p>}
          </div>
          {actions && <div style={{ display: 'flex', gap: '8px' }}>{actions}</div>}
        </div>
        {children}
      </main>
    </>
  );
}
