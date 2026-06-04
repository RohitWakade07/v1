import type { SessionStatus } from '@/types/api'
import { StatusBadge } from '@/components/shared/StatusBadge'

export const SessionStatusBadge = ({ status }: { status: SessionStatus }) => (
  <StatusBadge status={status} />
)
