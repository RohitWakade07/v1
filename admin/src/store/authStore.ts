import { create } from 'zustand'

interface AuthState {
  token: string | null
  username: string | null
  role: string | null
  setAuth: (token: string, username: string, role: string) => void
  logout: () => void
  hydrate: () => void
}

const TOKEN_KEY = 'sgp.admin.token'
const USERNAME_KEY = 'sgp.admin.username'
const ROLE_KEY = 'sgp.admin.role'

// BUG FIX: Decode JWT exp claim without a library.
// Previously hydrate() restored any stored token without checking
// whether it had already expired — a 401 was only discovered on
// the first API call, causing a flash of the dashboard before redirect.
const isTokenExpired = (token: string): boolean => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    // exp is in seconds; Date.now() is in milliseconds
    // Subtract 30s buffer so we don't use a token that will expire
    // mid-request during a slow network call.
    return payload.exp * 1000 < Date.now() + 30_000
  } catch {
    // Malformed token — treat as expired
    return true
  }
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  username: null,
  role: null,

  setAuth: (token, username, role) => {
    localStorage.setItem(TOKEN_KEY, token)
    localStorage.setItem(USERNAME_KEY, username)
    localStorage.setItem(ROLE_KEY, role)
    set({ token, username, role })
  },

  logout: () => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USERNAME_KEY)
    localStorage.removeItem(ROLE_KEY)
    set({ token: null, username: null, role: null })
  },

  hydrate: () => {
    const token = localStorage.getItem(TOKEN_KEY)
    const username = localStorage.getItem(USERNAME_KEY)
    const role = localStorage.getItem(ROLE_KEY)

    if (!token) return

    // BUG FIX: Skip restoring if token is expired or malformed
    if (isTokenExpired(token)) {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USERNAME_KEY)
      localStorage.removeItem(ROLE_KEY)
      return
    }

    set({ token, username, role })
  },
}))
