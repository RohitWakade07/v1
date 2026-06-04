import { useMutation, useQueryClient } from '@tanstack/react-query'
import { publishAssignment, unpublishAssignment } from '@/api/mentor/assignments'
import { useNotificationStore } from '@/store/notificationStore'

export function usePublishAssignment() {
  const queryClient = useQueryClient()
  const addNotification = useNotificationStore((s) => s.addNotification)
  
  return useMutation({
    mutationFn: publishAssignment,
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['assignments'] })
      queryClient.invalidateQueries({ queryKey: ['assignments', id] })
      addNotification({
        type: 'success',
        title: 'Assignment published',
        message: 'The assignment is now live for students.',
      })
    },
  })
}

export function useUnpublishAssignment() {
  const queryClient = useQueryClient()
  const addNotification = useNotificationStore((s) => s.addNotification)
  
  return useMutation({
    mutationFn: unpublishAssignment,
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['assignments'] })
      queryClient.invalidateQueries({ queryKey: ['assignments', id] })
      addNotification({
        type: 'success',
        title: 'Assignment unpublished',
        message: 'The assignment is now a draft and hidden from students.',
      })
    },
  })
}
