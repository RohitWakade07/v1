import { ShieldCheck, Key, Shield } from 'lucide-react'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { useAuthStore } from '@/store/authStore'
import { cn } from '@/lib/utils'

export const ProfilePage = () => {
  const { username, role, subjectId, mentorUuid } = useAuthStore()

  return (
    <PageWrapper>
      <PageHeader
        title="Profile & Security"
        description="View your mentor account details and active session information."
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card-dark p-6">
          <div className="mb-6 flex items-center gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-navy-800 text-2xl font-bold text-text-primary uppercase shadow-inner">
              {username?.charAt(0) || 'M'}
            </div>
            <div>
              <h2 className="font-display text-xl font-bold text-text-primary">{username}</h2>
              <div className="mt-1 flex items-center gap-2">
                <span className={cn(
                  "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-bold uppercase tracking-wider",
                  role === 'admin' 
                    ? "bg-accent-teal/10 text-accent-teal border border-accent-teal/20" 
                    : "bg-accent-blue/10 text-accent-blue border border-accent-blue/20"
                )}>
                  {role === 'admin' ? <Shield size={12} /> : <ShieldCheck size={12} />}
                  {role}
                </span>
              </div>
            </div>
          </div>

          <div className="space-y-4 border-t border-navy-800 pt-6">
            <div>
              <p className="text-xs font-medium uppercase tracking-wider text-text-secondary">Username</p>
              <p className="mt-1 font-medium text-text-primary">{username}</p>
            </div>
            
            <div className="pt-2">
              <p className="text-xs font-medium uppercase tracking-wider text-text-secondary">Account Role</p>
              <p className="mt-1 font-medium text-text-primary capitalize">{role}</p>
              <p className="mt-1 text-xs text-text-secondary">
                {role === 'admin' 
                  ? 'You have full administrative access to all platform capabilities.' 
                  : 'You have standard mentor access to create and manage assignments.'}
              </p>
            </div>
          </div>
        </div>

        <div className="card-dark p-6">
          <div className="mb-6 flex items-center gap-2">
            <Key className="text-text-secondary" size={20} />
            <h3 className="font-display text-lg font-semibold text-text-primary">Session Claims</h3>
          </div>
          
          <div className="rounded-lg bg-navy-950 p-4 border border-navy-800 font-mono text-sm space-y-3">
            <div className="flex flex-col">
              <span className="text-xs text-accent-blue">sub (Subject ID)</span>
              <span className="text-text-primary break-all">{subjectId || 'Not available'}</span>
            </div>
            
            <div className="flex flex-col">
              <span className="text-xs text-accent-blue">mentor_uuid</span>
              <span className="text-text-primary break-all">{mentorUuid || subjectId || 'Not available'}</span>
            </div>
            
            <div className="flex flex-col">
              <span className="text-xs text-accent-blue">role</span>
              <span className="text-text-primary">{role}</span>
            </div>
          </div>
          
          <div className="mt-4 rounded-lg bg-status-warning/10 border border-status-warning/20 p-4">
            <p className="text-xs text-status-warning">
              This information is extracted directly from your current JWT payload. It is used to authorize your actions against the Phase 1 backend API.
            </p>
          </div>
        </div>
      </div>
    </PageWrapper>
  )
}

export default ProfilePage
