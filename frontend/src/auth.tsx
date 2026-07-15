import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'

import { api, tokenStore } from './api'
import type { User } from './types'

interface AuthContextValue {
  user: User | null
  isReady: boolean
  signIn: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
  reloadProfile: () => Promise<void>
  hasRole: (...roles: string[]) => boolean
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isReady, setIsReady] = useState(false)

  const reloadProfile = useCallback(async () => {
    if (!tokenStore.getAccess()) {
      setUser(null)
      return
    }
    try {
      setUser(await api<User>('/profile'))
    } catch {
      tokenStore.clear()
      setUser(null)
    }
  }, [])

  useEffect(() => {
    reloadProfile().finally(() => setIsReady(true))
  }, [reloadProfile])

  const signIn = useCallback(async (email: string, password: string) => {
    const tokens = await api<{ access_token: string; refresh_token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    tokenStore.set(tokens.access_token, tokens.refresh_token)
    await reloadProfile()
  }, [reloadProfile])

  const signOut = useCallback(async () => {
    const refreshToken = tokenStore.getRefresh()
    try {
      if (refreshToken) {
        await api('/auth/logout', {
          method: 'POST',
          body: JSON.stringify({ refresh_token: refreshToken }),
        })
      }
    } finally {
      tokenStore.clear()
      setUser(null)
    }
  }, [])

  const value = useMemo<AuthContextValue>(() => ({
    user,
    isReady,
    signIn,
    signOut,
    reloadProfile,
    hasRole: (...roles) => Boolean(user?.roles.some((role) => roles.includes(role.name))),
  }), [isReady, reloadProfile, signIn, signOut, user])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside AuthProvider')
  return context
}

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, isReady } = useAuth()
  const location = useLocation()
  if (!isReady) return <div className="page-state">Loading your workspace…</div>
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />
  return <>{children}</>
}
