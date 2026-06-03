import { apiClient } from './client'
import type { ProofSubmitRequest, ProofSubmitResponse } from '@/types/api'

export const submitProof = async (payload: ProofSubmitRequest) => {
  const { data } = await apiClient.post<ProofSubmitResponse>('/proof/submit', payload, {
    headers: {
      'x-skip-error-toast': 'true',
    },
  })
  return data
}
