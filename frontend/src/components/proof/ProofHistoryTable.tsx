import { DataTable } from '@/components/shared/DataTable'

interface ProofHistoryItem {
  submittedAt: string
  status: string
  score?: string
}

interface ProofHistoryTableProps {
  history: ProofHistoryItem[]
}

export const ProofHistoryTable = ({ history }: ProofHistoryTableProps) => {
  const headers = ['Submitted', 'Status', 'Score']
  const rows = history.map((item) => [item.submittedAt, item.status, item.score])
  return <DataTable headers={headers} rows={rows} />
}
