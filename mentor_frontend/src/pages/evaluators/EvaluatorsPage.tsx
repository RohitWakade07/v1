import { Cpu } from 'lucide-react'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { ComingSoonPlaceholder } from '@/components/shared/ComingSoonPlaceholder'
import { AdminOnlyGuard } from '@/components/shared/AdminOnlyGuard'

export const EvaluatorsPage = () => {
  return (
    <PageWrapper>
      <PageHeader
        title="Evaluator Binaries"
        description="Manage, version, and distribute grader binaries for assignments."
      />
      <AdminOnlyGuard>
        <ComingSoonPlaceholder
          icon={Cpu}
          title="Grader Binary Management"
          description="A secure repository for uploading and versioning the executable grader binaries."
          capabilities={[
            'Upload new grader binary versions (Win/Mac/Linux)',
            'Cryptographic signing of binaries',
            'Bind specific binary versions to assignments',
            'Track binary download telemetry'
          ]}
        />
      </AdminOnlyGuard>
    </PageWrapper>
  )
}

export default EvaluatorsPage
