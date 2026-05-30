import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createAssignment } from '@/api/assignments'

export function useCreateAssignment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createAssignment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assignments'] })
    },
  })
}
