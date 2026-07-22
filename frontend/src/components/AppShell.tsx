import {
  BarChart3,
  Bell,
  CircleDollarSign,
  ClipboardCheck,
  Clock3,
  FileBarChart,
  FolderHeart,
  HandCoins,
  HeartHandshake,
  LayoutDashboard,
  LogOut,
  Menu,
  Package,
  Settings,
  UserCircle,
  Users,
  X,
} from 'lucide-react'
import { useEffect, useState, type ReactNode } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth'
import { brand } from '../branding'
import { LanguageSwitcher } from '../localization'

interface NavItem {
  label: string
  to: string
  icon: typeof LayoutDashboard
  roles?: string[]
}

const navigation: NavItem[] = [
  { label: brand.tabs.overview, to: '/dashboard', icon: LayoutDashboard, roles: ['admin', 'finance'] },
  { label: brand.tabs.donors, to: '/donors', icon: HeartHandshake },
  { label: brand.tabs.donations, to: '/donations', icon: HandCoins },
  { label: brand.tabs.donationTypes, to: '/donation-types', icon: CircleDollarSign, roles: ['admin', 'finance', 'viewer'] },
  { label: brand.tabs.warehouse, to: '/warehouse', icon: Package },
  { label: brand.tabs.cases, to: '/cases', icon: FolderHeart },
  { label: brand.tabs.custody, to: '/custody', icon: ClipboardCheck },
  { label: brand.tabs.approvals, to: '/approvals', icon: Bell, roles: ['admin', 'finance'] },
  { label: brand.tabs.reports, to: '/reports', icon: FileBarChart, roles: ['admin', 'finance', 'viewer'] },
  { label: brand.tabs.scheduledReports, to: '/reports/scheduled', icon: Clock3, roles: ['admin', 'finance'] },
  { label: brand.tabs.users, to: '/users', icon: Users, roles: ['admin'] },
]

export function AppShell({ children }: { children: ReactNode }) {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(
    () => window.localStorage.getItem('baytak-sidebar-collapsed') === 'true',
  )
  const { user, hasRole, signOut } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    window.localStorage.setItem('baytak-sidebar-collapsed', String(isSidebarCollapsed))
  }, [isSidebarCollapsed])

  const logout = async () => {
    await signOut()
    navigate('/')
  }

  const toggleNavigation = () => {
    if (window.matchMedia('(max-width: 800px)').matches) {
      setIsMenuOpen((isOpen) => !isOpen)
      return
    }
    setIsSidebarCollapsed((isCollapsed) => !isCollapsed)
  }

  return (
    <div className={`app-shell ${isSidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
      <aside className={`sidebar ${isMenuOpen ? 'sidebar-open' : ''}`}>
        <NavLink to="/dashboard" className="brand" onClick={() => setIsMenuOpen(false)}>
          <img className="brand-logo" src={brand.logoPath} alt={`${brand.appName} logo`} />
          <span className="brand-copy"><strong>{brand.appName}</strong><small>{brand.tagline}</small></span>
        </NavLink>
        <nav>
          <p className="nav-label">{brand.navigationTitle}</p>
          {navigation.filter((item) => !item.roles || hasRole(...item.roles)).map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                onClick={() => setIsMenuOpen(false)}
                title={item.label}
              >
                <Icon size={19} />
                <span className="nav-item-label">{item.label}</span>
              </NavLink>
            )
          })}
        </nav>
        <div className="sidebar-bottom">
          <NavLink to="/profile" className="nav-item" onClick={() => setIsMenuOpen(false)} title={brand.tabs.settings}>
            <Settings size={19} /> <span className="nav-item-label">{brand.tabs.settings}</span>
          </NavLink>
          <button type="button" className="account-switcher" onClick={() => navigate('/profile')}>
            <span className="avatar">{user?.first_name[0]}{user?.last_name[0]}</span>
            <span className="account-copy"><strong>{user?.first_name} {user?.last_name}</strong><small>{user?.roles[0]?.name ?? 'staff'}</small></span>
          </button>
        </div>
      </aside>
      {isMenuOpen && <button className="sidebar-backdrop" aria-label="Close navigation" onClick={() => setIsMenuOpen(false)} />}
      <main className="main-content">
        <header className="topbar">
          <button className="icon-button menu-button" type="button" aria-label={isMenuOpen ? 'Close navigation' : isSidebarCollapsed ? 'Expand navigation' : 'Collapse navigation'} onClick={toggleNavigation}>
            {isMenuOpen ? <X /> : <Menu />}
          </button>
          <div className="topbar-breadcrumb"><BarChart3 size={18} /> <span>{brand.appName}</span></div>
          <div className="topbar-actions">
            <LanguageSwitcher />
            <button className="icon-button" type="button" aria-label="Sign out" onClick={logout}><LogOut size={19} /></button>
          </div>
        </header>
        <div className="page-content">{children}</div>
      </main>
    </div>
  )
}

export function PageHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow?: string
  title: string
  description?: string
  action?: ReactNode
}) {
  return (
    <div className="page-header">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1>{title}</h1>
        {description && <p className="subtitle">{description}</p>}
      </div>
      {action && <div className="page-action">{action}</div>}
    </div>
  )
}

export function EmptyState({ title, message }: { title: string; message: string }) {
  return <div className="empty-state"><UserCircle size={28} /><strong>{title}</strong><span>{message}</span></div>
}
