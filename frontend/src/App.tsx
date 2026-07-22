import { BrowserRouter, Navigate, Outlet, Route, Routes } from 'react-router-dom'

import { AuthProvider, ProtectedRoute, useAuth } from './auth'
import { AppShell } from './components/AppShell'
import { LocaleProvider } from './localization'
import { ForgotPasswordPage, ResetPasswordPage } from './password-pages'
import {
  ApprovalsPage,
  CasesPage,
  CustodyPage,
  DashboardPage,
  DonationTypesPage,
  DonationsPage,
  DonorsPage,
  LandingPage,
  LoginPage,
  ProfilePage,
  ReportsPage,
  ScheduledReportsPage,
  UsersPage,
  WarehousePage,
} from './pages'

function AppLayout() {
  return <AppShell><Outlet /></AppShell>
}

function HomeRedirect() {
  const { hasRole } = useAuth()
  return <Navigate to={hasRole('admin', 'finance') ? '/dashboard' : '/donors'} replace />
}

function LoginRoute() {
  const { user, isReady } = useAuth()
  if (!isReady) return null
  return user ? <HomeRedirect /> : <LoginPage />
}

function App() {
  return (
    <BrowserRouter>
      <LocaleProvider>
        <AuthProvider>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginRoute />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
            <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/donors" element={<DonorsPage />} />
              <Route path="/donations" element={<DonationsPage />} />
              <Route path="/donation-types" element={<DonationTypesPage />} />
              <Route path="/warehouse" element={<WarehousePage />} />
              <Route path="/cases" element={<CasesPage />} />
              <Route path="/custody" element={<CustodyPage />} />
              <Route path="/approvals" element={<ApprovalsPage />} />
              <Route path="/reports" element={<ReportsPage />} />
              <Route path="/reports/scheduled" element={<ScheduledReportsPage />} />
              <Route path="/users" element={<UsersPage />} />
              <Route path="/profile" element={<ProfilePage />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </LocaleProvider>
    </BrowserRouter>
  )
}

export default App
