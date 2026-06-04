import { useMutation, useQueryClient } from '@tanstack/react-query'
import { submitProof, submitEepProof } from '@/api/student/proof'
import { useNotificationStore } from '@/store/notificationStore'
function parseApiDetail(error: unknown): string {
  const responseData = (error as { response?: { data?: { detail?: unknown } } })?.response?.data
  if (!responseData?.detail) {
    return 'Submission failed. Please try again.'
  }
  if (typeof responseData.detail === 'string') {
    return responseData.detail
  }
  if (Array.isArray(responseData.detail)) {
    return responseData.detail
      .map((err: { loc?: string[]; msg?: string }) => {
        const field = err.loc?.length ? err.loc[err.loc.length - 1] : 'field'
        return `"${field}" ${err.msg ?? 'invalid'}`
      })
      .join(', ')
  }
  return 'Submission failed. Please try again.'
}

export const useProofSubmit = () =>
  useMutation({
    mutationFn: submitProof,
  })

export const useEepProofSubmit = () => {
  const queryClient = useQueryClient()
  const addNotification = useNotificationStore((s) => s.addNotification)

  return useMutation({
    mutationFn: ({ sessionId, file }: { sessionId: string; file: File }) =>
      submitEepProof(sessionId, file),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] })
      queryClient.invalidateQueries({ queryKey: ['results'] })
      addNotification({
        type: 'success',
        title: 'EEP submission verified',
        message: response.message,
      })
    },
    onError: (error) => {
      const message = parseApiDetail(error)
      addNotification({
        type: 'error',
        title: 'EEP submission failed',
        message,
      })
    },
  })
}
