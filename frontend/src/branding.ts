const environment = import.meta.env

function value(key: string, fallback: string) {
  const configured = environment[key]
  return typeof configured === 'string' && configured.trim() ? configured.trim() : fallback
}

export const brand = {
  appName: value('VITE_APP_NAME', 'Baytak Foundation'),
  shortName: value('VITE_APP_SHORT_NAME', 'Baytak'),
  tagline: value('VITE_APP_TAGLINE', 'Community charity management'),
  description: value(
    'VITE_APP_DESCRIPTION',
    'Transparent, people-first charity operations.',
  ),
  contactEmail: value('VITE_APP_CONTACT_EMAIL', 'info@baytakfoundation.org'),
  logoPath: value('VITE_APP_LOGO_PATH', '/baytak-logo.png'),
  defaultLocale: value('VITE_DEFAULT_LOCALE', 'ar') === 'en' ? 'en' as const : 'ar' as const,
  navigationTitle: value('VITE_NAVIGATION_TITLE', 'Workspace'),
  tabs: {
    overview: value('VITE_TAB_OVERVIEW', 'Overview'),
    donors: value('VITE_TAB_DONORS', 'Donors'),
    donations: value('VITE_TAB_DONATIONS', 'Donations'),
    donationTypes: value('VITE_TAB_DONATION_TYPES', 'Donation types'),
    warehouse: value('VITE_TAB_WAREHOUSE', 'Warehouse'),
    cases: value('VITE_TAB_CASES', 'Cases'),
    activities: value('VITE_TAB_ACTIVITIES', 'المشروعات'),
    custody: value('VITE_TAB_CUSTODY', 'Custody'),
    approvals: value('VITE_TAB_APPROVALS', 'Approvals'),
    reports: value('VITE_TAB_REPORTS', 'Reports'),
    scheduledReports: value('VITE_TAB_SCHEDULED_REPORTS', 'Scheduled reports'),
    users: value('VITE_TAB_USERS', 'Users'),
    settings: value('VITE_TAB_SETTINGS', 'Settings'),
  },
  colors: {
    primary: value('VITE_COLOR_PRIMARY', '#1765a7'),
    primaryDark: value('VITE_COLOR_PRIMARY_DARK', '#104e85'),
    accent: value('VITE_COLOR_ACCENT', '#2a78ba'),
    sidebar: value('VITE_COLOR_SIDEBAR', '#123b65'),
    background: value('VITE_COLOR_BACKGROUND', '#f5f8fc'),
    surface: value('VITE_COLOR_SURFACE', '#ffffff'),
    text: value('VITE_COLOR_TEXT', '#162b3d'),
    mutedText: value('VITE_COLOR_MUTED_TEXT', '#607285'),
    success: value('VITE_COLOR_SUCCESS', '#167044'),
    warning: value('VITE_COLOR_WARNING', '#a86b09'),
    danger: value('VITE_COLOR_DANGER', '#ae3f34'),
  },
}

export function applyBranding() {
  document.title = brand.appName
  document.querySelector('meta[name="description"]')?.setAttribute('content', brand.description)
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', brand.colors.primary)
  const root = document.documentElement
  root.style.setProperty('--brand-primary', brand.colors.primary)
  root.style.setProperty('--brand-primary-dark', brand.colors.primaryDark)
  root.style.setProperty('--brand-accent', brand.colors.accent)
  root.style.setProperty('--brand-sidebar', brand.colors.sidebar)
  root.style.setProperty('--color-background', brand.colors.background)
  root.style.setProperty('--color-surface', brand.colors.surface)
  root.style.setProperty('--color-text', brand.colors.text)
  root.style.setProperty('--color-muted-text', brand.colors.mutedText)
  root.style.setProperty('--color-success', brand.colors.success)
  root.style.setProperty('--color-warning', brand.colors.warning)
  root.style.setProperty('--color-danger', brand.colors.danger)
}
