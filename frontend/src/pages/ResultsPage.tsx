import { PageWrapper } from '@/components/layout/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { useResults } from '@/hooks/useResults'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'
import { EmptyState } from '@/components/shared/EmptyState'
import { ResultCard } from '@/components/results/ResultCard'

const ResultsPage = () => {
  const { data, isLoading } = useResults()

  if (isLoading) return <LoadingSpinner />

  const results = data ?? []

  return (
    <PageWrapper>
      <PageHeader
        title="Results"
        description="Browse completed evaluations and score breakdowns."
      />
      {results.length === 0 ? (
        <EmptyState
          title="No results yet"
          message="Once an evaluation is verified, results appear here."
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {results.map((result) => (
            <ResultCard key={result.id} result={result} />
          ))}
        </div>
      )}
    </PageWrapper>
  )
}

export default ResultsPage
