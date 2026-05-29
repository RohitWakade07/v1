import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { ProofDropZone } from '@/components/proof/ProofDropZone'
import { ProofUploadProgress } from '@/components/proof/ProofUploadProgress'
import { ProofHistoryTable } from '@/components/proof/ProofHistoryTable'
import { useSessions } from '@/hooks/useSessions'
import { useProofSubmit } from '@/hooks/useProofSubmit'
import { proofFileSchema } from '@/lib/schemas'
import type { ProofSubmitRequest } from '@/types/api'
import { useNotificationStore } from '@/store/notificationStore'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'

const ProofSubmitPage = () => {
  const { data: sessions, isLoading } = useSessions()
  const [selectedSessionId, setSelectedSessionId] = useState<string>('')
  const [fileName, setFileName] = useState<string>('')
  const [parsedProof, setParsedProof] = useState<ProofSubmitRequest | null>(null)
  const [status, setStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>(
    'idle',
  )
  const [statusMessage, setStatusMessage] = useState('')
  const proofSubmit = useProofSubmit()
  const addNotification = useNotificationStore((state) => state.addNotification)
  const location = useLocation()

  const activeSessions = (sessions ?? []).filter((session) =>
    ['STARTED', 'IN_PROGRESS'].includes(session.status),
  )

  const searchParams = new URLSearchParams(location.search)
  const preselectedSession = searchParams.get('session_id')

  useEffect(() => {
    if (preselectedSession) {
      setSelectedSessionId(preselectedSession)
    }
  }, [preselectedSession])

  const handleFileSelected = (file: File) => {
    if (file.size > 5 * 1024 * 1024) {
      setStatus('error')
      setStatusMessage('Proof file exceeds 5MB limit.')
      return
    }
    setFileName(file.name)
    const reader = new FileReader()
    reader.onload = () => {
      try {
        const parsed = JSON.parse(reader.result as string)
        const validation = proofFileSchema.safeParse(parsed)
        if (!validation.success) {
          setStatus('error')
          setStatusMessage('Proof file is missing required fields.')
          setParsedProof(null)
          return
        }
        setParsedProof(validation.data as ProofSubmitRequest)
        setStatus('idle')
        setStatusMessage('')
      } catch (error) {
        setStatus('error')
        setStatusMessage('Unable to parse JSON file.')
        setParsedProof(null)
      }
    }
    reader.readAsText(file)
  }

  const handleSubmit = async () => {
    if (!parsedProof || !selectedSessionId) return
    setStatus('uploading')
    setStatusMessage('Submitting proof package...')
    try {
      const response = await proofSubmit.mutateAsync(parsedProof)
      setStatus('success')
      setStatusMessage(response.message)
      addNotification({
        type: response.status === 'COMPLETED' ? 'success' : 'warning',
        title: 'Proof submitted',
        message: response.message,
      })
    } catch (error) {
      setStatus('error')
      setStatusMessage('Submission failed. Please try again.')
    }
  }

  if (isLoading) return <LoadingSpinner />

  return (
    <PageWrapper>
      <PageHeader
        title="Submit Proof"
        description="Upload your signed proof.json file for verification."
      />
      <div className="rounded-xl border border-navy-800 bg-navy-900/50 p-5 shadow-card">
        <label className="text-sm text-text-secondary">Select Session</label>
        <select
          className="mt-2 w-full rounded-lg border border-navy-800 bg-navy-950 px-3 py-2 text-text-primary"
          value={selectedSessionId}
          onChange={(event) => setSelectedSessionId(event.target.value)}
        >
          <option value="">Select an active session</option>
          {activeSessions.map((session) => (
            <option key={session.id} value={session.id}>
              {session.id}
            </option>
          ))}
        </select>
      </div>
      <ProofDropZone onFileSelected={handleFileSelected} fileName={fileName} />
      {parsedProof && (
        <div className="rounded-xl border border-navy-800 bg-navy-900/50 p-5 text-sm text-text-secondary shadow-card">
          <h3 className="font-display text-lg font-semibold text-text-primary">
            Proof Preview
          </h3>
          <div className="mt-3 grid gap-2">
            <div>Session ID: <span className="font-mono">{parsedProof.session_id}</span></div>
            <div>Assignment ID: <span className="font-mono">{parsedProof.assignment_id}</span></div>
            <div>Student ID: <span className="font-mono">{parsedProof.student_id}</span></div>
            <div>Nonce: <span className="font-mono">{parsedProof.nonce}</span></div>
            <div>Grader Hash: <span className="font-mono">{parsedProof.grader_binary_hash}</span></div>
            <div>Tests: {Object.keys(parsedProof.results).length}</div>
          </div>
        </div>
      )}
      <div className="flex items-center gap-4">
        <button
          className="rounded-lg bg-accent-blue px-4 py-2 text-sm font-medium text-white"
          onClick={handleSubmit}
          disabled={!parsedProof || !selectedSessionId || proofSubmit.isPending}
        >
          {proofSubmit.isPending ? 'Submitting...' : 'Submit Proof'}
        </button>
        <ProofUploadProgress status={status} message={statusMessage} />
      </div>
      <div className="rounded-xl border border-navy-800 bg-navy-900/50 p-5 shadow-card">
        <h3 className="font-display text-lg font-semibold text-text-primary">
          Proof History
        </h3>
        <div className="mt-4">
          <ProofHistoryTable
            history={[]}
          />
        </div>
      </div>
    </PageWrapper>
  )
}

export default ProofSubmitPage
