import { create } from 'zustand'
import type { StudentProfile } from '@/types/api'

interface AuthState {
  token: string | null
  profile: StudentProfile | null
  setToken: (token: string | null) => void
  setProfile: (profile: StudentProfile | null) => void
  hydrate: () => void
  logout: () => void
}

const storageKey = 'sgp.student.token'

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  profile: null,
  setToken: (token) => {
    if (token) {
      localStorage.setItem(storageKey, token)
    } else {
      localStorage.removeItem(storageKey)
    }
    set({ token })
  },
  setProfile: (profile) => set({ profile }),
  hydrate: () => {
    const token = localStorage.getItem(storageKey)
    if (token) {
      set({ token })
    }
  },
  logout: () => {
    localStorage.removeItem(storageKey)
    set({ token: null, profile: null })
  },
}))
