import { apiClient } from '@/api/client'
import type {
  SubmissionCreateResponse,
  SubmissionPublic,
  SubmissionSourceType,
  SubmissionResultDetail,
} from '@/types/api'

export const submitAssignment = async (
  assignmentId: string,
  sourceType: SubmissionSourceType,
  repoUrl?: string,
  file?: File,
): Promise<SubmissionCreateResponse> => {
  const formData = new FormData()
  formData.append('assignment_id', assignmentId)
  formData.append('source_type', sourceType)
  if (repoUrl && sourceType === 'github') {
    formData.append('repo_url', repoUrl)
  }
  if (file && sourceType === 'zip') {
    formData.append('file', file)
  }

  const { data } = await apiClient.post<SubmissionCreateResponse>(
    '/submissions',
    formData,
    {
      headers: {
        'Content-Type': undefined,
        'x-skip-error-toast': 'true',
      },
    },
  )
  return data
}

export const listSubmissions = async (): Promise<SubmissionPublic[]> => {
  const { data } = await apiClient.get<SubmissionPublic[]>('/submissions')
  return data
}

export const getSubmission = async (id: string): Promise<SubmissionPublic> => {
  const { data } = await apiClient.get<SubmissionPublic>(`/submissions/${id}`)
  return data
}

export const getSubmissionResult = async (id: string): Promise<SubmissionResultDetail> => {
  const { data } = await apiClient.get<SubmissionResultDetail>(`/submissions/${id}/result`)
  return data
}

export const cancelSubmission = async (id: string): Promise<SubmissionPublic> => {
  const { data } = await apiClient.post<SubmissionPublic>(`/submissions/${id}/cancel`)
  return data
}
