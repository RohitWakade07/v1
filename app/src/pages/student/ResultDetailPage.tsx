import { useParams } from 'react-router-dom'
import { PageWrapper } from '@/components/shared/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { useResult } from '@/hooks/student/useResults'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'
import { Trophy } from 'lucide-react'
import { ScoreBreakdownTable } from '@/components/student/results/ScoreBreakdownTable'
import { CertificateDownloadButton } from '@/components/student/results/CertificateDownloadButton'

const ResultDetailPage = () => {
  const { id } = useParams()
  const { data, isLoading } = useResult(id)

  if (isLoading) return <LoadingSpinner />
  if (!data) return null

  const percent = (data.final_score / data.max_score) * 100

  return (
    <PageWrapper>
      <PageHeader
        title="Result Detail"
        description="Verified scores and breakdown by test case."
        actions={<CertificateDownloadButton disabled />}
      />
      <div className="rounded-xl border border-navy-800 bg-navy-900/50 p-6 shadow-card">
        <div className="flex items-center gap-4">
          <Trophy className="text-accent-teal" size={30} />
          <div>
            <p className="text-xs text-text-secondary">Final Score</p>
            <p className="font-display text-3xl font-semibold text-text-primary">
              {data.final_score.toFixed(1)} / {data.max_score.toFixed(1)}
            </p>
            <p className="text-sm text-text-secondary">
              {percent.toFixed(1)}% achieved
            </p>
          </div>
        </div>
      </div>
      <ScoreBreakdownTable breakdown={data.score_breakdown} />
    </PageWrapper>
  )
}

export default ResultDetailPage
