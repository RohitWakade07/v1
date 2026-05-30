import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { UserRole } from '@/types/api'

interface AuthState {
  token: string | null
  role: UserRole | null
  subjectId: string | null
  username: string | null
  mentorUuid: string | null
  isAuthenticated: boolean
  login: (token: string, role: UserRole, subjectId: string, username: string, mentorUuid: string) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      role: null,
      subjectId: null,
      username: null,
      mentorUuid: null,
      isAuthenticated: false,
      login: (token, role, subjectId, username, mentorUuid) =>
        set({ token, role, subjectId, username, mentorUuid, isAuthenticated: true }),
      logout: () =>
        set({
          token: null,
          role: null,
          subjectId: null,
          username: null,
          mentorUuid: null,
          isAuthenticated: false,
        }),
    }),
    {
      name: 'mentor-auth-storage',
    },
  ),
)
