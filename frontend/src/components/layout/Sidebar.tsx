/**
 * Sidebar navigation component.
 * Institutional design — deep navy, saffron active indicator.
 */

import { NavLink } from 'react-router-dom';

interface NavItem {
  to: string;
  label: string;
  icon: string;
  section?: string;
}

const navItems: NavItem[] = [
  { to: '/',           label: 'Dashboard',       icon: '📊', section: 'Overview' },
  { to: '/upload',     label: 'Upload Data',     icon: '📁', section: 'Data' },
  { to: '/batch',      label: 'Batch Overview',  icon: '📋', section: 'Data' },
  { to: '/anomaly',    label: 'Anomaly Results', icon: '⚠️',  section: 'Analysis' },
  { to: '/drift',      label: 'Drift Results',   icon: '📈', section: 'Analysis' },
  { to: '/component',  label: 'Component Detail',icon: '🔍', section: 'Analysis' },
  { to: '/metrics',    label: 'Model Metrics',   icon: '📐', section: 'Evaluation' },
  { to: '/report',     label: 'QA Report',       icon: '📄', section: 'Output' },
];

export default function Sidebar() {
  // Group items by section
  const sections: Record<string, NavItem[]> = {};
  for (const item of navItems) {
    const sec = item.section || 'General';
    if (!sections[sec]) sections[sec] = [];
    sections[sec].push(item);
  }

  return (
    <aside className="app-sidebar" role="navigation" aria-label="Main navigation">
      <div className="sidebar-header">
        <div className="sidebar-title">Burn-In Screening</div>
        <div className="sidebar-subtitle">Anomaly Detection System</div>
      </div>

      <nav className="sidebar-nav">
        {Object.entries(sections).map(([section, items]) => (
          <div key={section}>
            <div className="sidebar-section-label">{section}</div>
            {items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  `sidebar-link${isActive ? ' active' : ''}`
                }
              >
                <span className="sidebar-link-icon" aria-hidden="true">{item.icon}</span>
                {item.label}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        Prototype v0.1.0<br />
        Not an official ISRO system
      </div>
    </aside>
  );
}
