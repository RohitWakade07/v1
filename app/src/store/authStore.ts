import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { StudentProfile, UserRole } from '@/types/api'
import { isTokenExpired } from '@/lib/utils'

interface AuthState {
  // Shared
  token: string | null
  role: UserRole | null
  isAuthenticated: boolean

  // Student-specific
  profile: StudentProfile | null

  // Mentor/Admin-specific
  username: string | null
  subjectId: string | null
  mentorUuid: string | null

  // Actions
  loginStudent: (token: string, profile: StudentProfile) => void
  loginStaff: (
    token: string,
    role: 'mentor' | 'admin',
    username: string,
    subjectId: string,
    mentorUuid?: string,
  ) => void
  setProfile: (profile: StudentProfile | null) => void
  logout: () => void
  hydrate: () => void
}

const TOKEN_KEY = 'sgp.token'

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      role: null,
      isAuthenticated: false,
      profile: null,
      username: null,
      subjectId: null,
      mentorUuid: null,

      loginStudent: (token, profile) =>
        set({
          token,
          role: 'student',
          isAuthenticated: true,
          profile,
          username: null,
          subjectId: null,
          mentorUuid: null,
        }),

      loginStaff: (token, role, username, subjectId, mentorUuid) =>
        set({
          token,
          role,
          isAuthenticated: true,
          profile: null,
          username,
          subjectId,
          mentorUuid: mentorUuid ?? null,
        }),

      setProfile: (profile) => set({ profile }),

      logout: () =>
        set({
          token: null,
          role: null,
          isAuthenticated: false,
          profile: null,
          username: null,
          subjectId: null,
          mentorUuid: null,
        }),

      // Validates stored token on app load — clears if expired
      hydrate: () => {
        const token = localStorage.getItem(TOKEN_KEY)
        if (!token) return
        if (isTokenExpired(token)) {
          localStorage.removeItem(TOKEN_KEY)
        }
        // zustand/persist already restores the rest of the state from storage
      },
    }),
    {
      name: 'sgp-auth',
      // Only persist these fields; exclude hydrate/actions
      partialize: (state) => ({
        token: state.token,
        role: state.role,
        isAuthenticated: state.isAuthenticated,
        profile: state.profile,
        username: state.username,
        subjectId: state.subjectId,
        mentorUuid: state.mentorUuid,
      }),
      onRehydrateStorage: () => (state) => {
        // On rehydration, check if the restored token has expired
        if (state?.token && isTokenExpired(state.token)) {
          state.logout()
        }
      },
    },
  ),
)
