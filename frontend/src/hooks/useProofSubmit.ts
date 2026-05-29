import { useMutation } from '@tanstack/react-query'
import { submitProof } from '@/api/proof'

export const useProofSubmit = () =>
  useMutation({
    mutationFn: submitProof,
  })
