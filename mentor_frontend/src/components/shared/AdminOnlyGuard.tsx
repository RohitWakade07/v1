import { useAuthStore } from '@/store/authStore'
import { ShieldAlert } from 'lucide-react'

export const AdminOnlyGuard = ({ children }: { children: React.ReactNode }) => {
  const role = useAuthStore((s) => s.role)

  if (role !== 'admin') {
    return (
      <div className="flex items-center gap-3 rounded-lg border border-status-warning/30 bg-status-warning/10 p-4 text-status-warning">
        <ShieldAlert size={20} className="shrink-0" />
        <p className="text-sm font-medium">Admin access required for this feature.</p>
      </div>
    )
  }

  return <>{children}</>
}
