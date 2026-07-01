import { apiClient } from '@/api/client'
import type { ProofSubmitResponse } from '@/types/api'


export const submitEepProof = async (
  sessionId: string,
  file: File,
): Promise<ProofSubmitResponse> => {
  const formData = new FormData()
  formData.append('session_id', sessionId)
  formData.append('file', file)
  const { data } = await apiClient.post<ProofSubmitResponse>(
    '/proof/submit-eep',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
        'x-skip-error-toast': 'true',
      },
    },
  )
  return data
}
