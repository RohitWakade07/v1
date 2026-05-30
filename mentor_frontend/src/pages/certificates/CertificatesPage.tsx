import { Award } from 'lucide-react'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { ComingSoonPlaceholder } from '@/components/shared/ComingSoonPlaceholder'
import { AdminOnlyGuard } from '@/components/shared/AdminOnlyGuard'

export const CertificatesPage = () => {
  return (
    <PageWrapper>
      <PageHeader
        title="Certificates"
        description="Issue, revoke, and manage cryptographic certificates for students."
      />
      <AdminOnlyGuard>
        <ComingSoonPlaceholder
          icon={Award}
          title="Certificate Issuance"
          description="A centralized system for generating and managing completion certificates."
          capabilities={[
            'Automated certificate generation based on score thresholds',
            'Cryptographic signing of issued certificates',
            'Certificate revocation management',
            'Public verification endpoint configuration'
          ]}
        />
      </AdminOnlyGuard>
    </PageWrapper>
  )
}

export default CertificatesPage
