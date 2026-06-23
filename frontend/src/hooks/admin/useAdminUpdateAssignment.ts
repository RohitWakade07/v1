import { useMutation, useQueryClient } from '@tanstack/react-query'
import { adminUpdateAssignment, AdminAssignmentUpdate } from '@/api/admin/admin'
import { useNotificationStore } from '@/store/notificationStore'

export function useAdminUpdateAssignment() {
  const queryClient = useQueryClient()
  const addNotification = useNotificationStore((s) => s.addNotification)
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: AdminAssignmentUpdate }) => adminUpdateAssignment(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-assignments'] })
      queryClient.invalidateQueries({ queryKey: ['assignments'] })
      addNotification({
        type: 'success',
        title: 'Assignment updated',
        message: 'The assignment details have been saved.',
      })
    },
    onError: () => {
      addNotification({
        type: 'error',
        title: 'Update failed',
        message: 'Failed to update assignment details.',
      })
    }
  })
}
