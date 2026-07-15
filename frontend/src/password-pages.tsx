import { useMutation } from '@tanstack/react-query'
import { ArrowLeft, KeyRound, MailCheck } from 'lucide-react'
import { useState, type FormEvent, type ReactNode } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { api, ApiError } from './api'
import { brand } from './branding'
import { LanguageSwitcher } from './localization'

function errorMessage(error: unknown) {
  return error instanceof ApiError ? error.message : 'Something went wrong. Please try again.'
}

function PasswordHelpLayout({ children }: { children: ReactNode }) {
  const navigate = useNavigate()
  return (
    <div className="auth-page password-help-page">
      <section className="auth-intro">
        <button type="button" className="brand brand-button" onClick={() => navigate('/')}>
          <img className="brand-logo" src={brand.logoPath} alt={`${brand.appName} logo`} />
          <span><strong>{brand.appName}</strong><small>{brand.tagline}</small></span>
        </button>
        <div>
          <p className="eyebrow">Account recovery</p>
          <h1>Keep access to the work that matters.</h1>
          <p>Use your organisation email to securely restore access to your account.</p>
        </div>
      </section>
      <section className="auth-card-wrap">{children}</section>
    </div>
  )
}

export function ForgotPasswordPage() {
  const navigate = useNavigate()
  const [notice, setNotice] = useState<string | null>(null)
  const requestReset = useMutation({
    mutationFn: (email: string) => api<{ message: string }>('/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email }),
    }),
    onSuccess: (result) => setNotice(result.message),
  })

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    requestReset.mutate(String(new FormData(event.currentTarget).get('email')))
  }

  return (
    <PasswordHelpLayout>
      <form className="auth-card password-help-card" onSubmit={submit}>
        <div className="auth-card-heading">
          <div><p className="eyebrow">Password reset</p><h2>Reset your password</h2><p>We will email a secure, time-limited reset link to your organisation address.</p></div>
          <LanguageSwitcher />
        </div>
        {notice ? (
          <div className="email-success">
            <MailCheck size={25} />
            <strong>Check your email</strong>
            <p>{notice}</p>
          </div>
        ) : (
          <>
            <label>Email<input name="email" type="email" required autoComplete="email" autoFocus /></label>
            {requestReset.error && <p className="form-error">{errorMessage(requestReset.error)}</p>}
            <button className="button button-primary button-full" disabled={requestReset.isPending}>
              <MailCheck size={18} /> {requestReset.isPending ? 'Sending…' : 'Send reset link'}
            </button>
          </>
        )}
        <button className="text-button back-link" type="button" onClick={() => navigate('/login')}><ArrowLeft size={16} /> Back to sign in</button>
      </form>
    </PasswordHelpLayout>
  )
}

export function ResetPasswordPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [formError, setFormError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const token = searchParams.get('token')
  const resetPassword = useMutation({
    mutationFn: (newPassword: string) => api<{ message: string }>('/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify({ token, new_password: newPassword }),
    }),
    onSuccess: (result) => setNotice(result.message),
  })

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const password = String(form.get('password'))
    const confirmation = String(form.get('confirmation'))
    if (!token) {
      setFormError('This password reset link is invalid or incomplete.')
      return
    }
    if (password !== confirmation) {
      setFormError('The two passwords do not match.')
      return
    }
    setFormError(null)
    resetPassword.mutate(password)
  }

  return (
    <PasswordHelpLayout>
      <form className="auth-card password-help-card" onSubmit={submit}>
        <div className="auth-card-heading">
          <div><p className="eyebrow">Choose a new password</p><h2>Set a new password</h2><p>Choose a unique password with at least 8 characters.</p></div>
          <LanguageSwitcher />
        </div>
        {notice ? (
          <div className="email-success">
            <KeyRound size={25} />
            <strong>Password updated</strong>
            <p>{notice}</p>
            <button className="button button-primary button-full" type="button" onClick={() => navigate('/login')}>Sign in</button>
          </div>
        ) : (
          <>
            <label>New password<input name="password" type="password" minLength={8} required autoFocus autoComplete="new-password" /></label>
            <label>Confirm new password<input name="confirmation" type="password" minLength={8} required autoComplete="new-password" /></label>
            {(formError || resetPassword.error) && <p className="form-error">{formError ?? errorMessage(resetPassword.error)}</p>}
            <button className="button button-primary button-full" disabled={resetPassword.isPending}>
              <KeyRound size={18} /> {resetPassword.isPending ? 'Updating…' : 'Update password'}
            </button>
          </>
        )}
        {!notice && <button className="text-button back-link" type="button" onClick={() => navigate('/login')}><ArrowLeft size={16} /> Back to sign in</button>}
      </form>
    </PasswordHelpLayout>
  )
}
