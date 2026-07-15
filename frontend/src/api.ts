const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'
const ACCESS_TOKEN_KEY = 'charity.access-token'
const REFRESH_TOKEN_KEY = 'charity.refresh-token'

let refreshPromise: Promise<string | null> | null = null

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

export const tokenStore = {
  getAccess: () => localStorage.getItem(ACCESS_TOKEN_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_TOKEN_KEY),
  set: (accessToken: string, refreshToken: string) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
  },
  clear: () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  },
}

async function errorFrom(response: Response): Promise<ApiError> {
  const body = await response.json().catch(() => null)
  return new ApiError(body?.detail ?? `Request failed (${response.status})`, response.status)
}

async function refreshAccessToken(): Promise<string | null> {
  if (refreshPromise) return refreshPromise
  const refreshToken = tokenStore.getRefresh()
  if (!refreshToken) return null

  refreshPromise = fetch(`${API_BASE_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })
    .then(async (response) => {
      if (!response.ok) throw await errorFrom(response)
      const tokens = await response.json()
      tokenStore.set(tokens.access_token, tokens.refresh_token)
      return tokens.access_token as string
    })
    .catch(() => {
      tokenStore.clear()
      return null
    })
    .finally(() => {
      refreshPromise = null
    })
  return refreshPromise
}

async function authorizedFetch(
  path: string,
  init: RequestInit = {},
  retry = true,
): Promise<Response> {
  const headers = new Headers(init.headers)
  const accessToken = tokenStore.getAccess()
  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`)
  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers })
  if (response.status === 401 && retry && !path.startsWith('/auth/')) {
    const replacementToken = await refreshAccessToken()
    if (replacementToken) return authorizedFetch(path, init, false)
  }
  return response
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  if (init.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  const response = await authorizedFetch(path, { ...init, headers })
  if (!response.ok) throw await errorFrom(response)
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export async function download(path: string, filename: string): Promise<void> {
  const response = await authorizedFetch(path)
  if (!response.ok) throw await errorFrom(response)
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}
