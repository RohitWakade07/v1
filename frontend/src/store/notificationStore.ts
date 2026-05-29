import { create } from 'zustand'

export type NotificationType = 'success' | 'error' | 'warning' | 'info'

export interface NotificationItem {
  id: string
  type: NotificationType
  title: string
  message: string
}

interface NotificationState {
  notifications: NotificationItem[]
  addNotification: (item: Omit<NotificationItem, 'id'>) => void
  removeNotification: (id: string) => void
  clearNotifications: () => void
}

export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: [],
  addNotification: (item) => {
    const id = crypto.randomUUID()
    set((state) => ({
      notifications: [{ ...item, id }, ...state.notifications],
    }))
  },
  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((note) => note.id !== id),
    })),
  clearNotifications: () => set({ notifications: [] }),
}))
