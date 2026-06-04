import { apiClient } from '@/api/client'
import type { ProofSubmitRequest, ProofSubmitResponse } from '@/types/api'

export const submitProof = async (payload: ProofSubmitRequest): Promise<ProofSubmitResponse> => {
  const { data } = await apiClient.post<ProofSubmitResponse>('/proof/submit', payload, {
    headers: { 'x-skip-error-toast': 'true' },
  })
  return data
}

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
    { headers: { 'x-skip-error-toast': 'true' } },
  )
  return data
}
