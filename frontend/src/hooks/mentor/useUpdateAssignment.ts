import { useMutation, useQueryClient } from '@tanstack/react-query'
import { updateAssignment, AssignmentUpdate } from '@/api/mentor/assignments'
import { useNotificationStore } from '@/store/notificationStore'

export function useUpdateAssignment() {
  const queryClient = useQueryClient()
  const addNotification = useNotificationStore((s) => s.addNotification)
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: AssignmentUpdate }) => updateAssignment(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['assignments'] })
      queryClient.invalidateQueries({ queryKey: ['assignments', variables.id] })
      addNotification({
        type: 'success',
        title: 'Assignment updated',
        message: 'The assignment details have been saved.',
      })
    },
  })
}
