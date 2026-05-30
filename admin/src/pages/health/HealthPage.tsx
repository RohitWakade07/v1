import { useQuery } from '@tanstack/react-query'
import { HeartPulse, Database, CheckCircle, XCircle, RefreshCw } from 'lucide-react'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { getHealth } from '@/api/health'

export const HealthPage = () => {
  const { data: health, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
    retry: 1,
  })

  const isOperational = health?.status === 'ok'
  const dbOk = health?.database === 'ok'

  return (
    <PageWrapper>
      <PageHeader
        title="Platform Health"
        description="Real-time status of backend services"
        actions={
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="btn-secondary"
          >
            <RefreshCw size={14} className={isFetching ? 'animate-spin-custom' : ''} />
            Refresh
          </button>
        }
      />

      {/* Overall status banner */}
      <div className={`mb-6 rounded-xl border p-5 flex items-center gap-4 animate-fade-in-up ${
        isLoading
          ? 'border-navy-800 bg-navy-900'
          : isOperational
          ? 'border-accent-teal/30 bg-accent-teal/5'
          : 'border-status-danger/30 bg-status-danger/5'
      }`}>
        <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${
          isLoading ? 'bg-navy-800' : isOperational ? 'bg-accent-teal/15' : 'bg-status-danger/15'
        }`}>
          <HeartPulse size={24} className={
            isLoading ? 'text-text-secondary' : isOperational ? 'text-accent-teal' : 'text-status-danger'
          } />
        </div>
        <div>
          <p className="font-display text-lg font-bold text-text-primary">
            {isLoading ? 'Checking…' : isOperational ? 'All Systems Operational' : error ? 'Backend Unreachable' : 'Degraded'}
          </p>
          <p className="text-sm text-text-secondary">
            {isLoading ? 'Pinging backend…' : isOperational
              ? 'API and database are healthy'
              : 'One or more services are not responding'}
          </p>
        </div>
        {!isLoading && (
          <div className={`ml-auto flex h-3 w-3 rounded-full ${isOperational ? 'bg-accent-teal animate-pulse' : 'bg-status-danger'}`} />
        )}
      </div>

      {/* Service cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {/* API */}
        <div className="card-dark p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-semibold tracking-widest text-text-secondary uppercase">API Server</p>
              <p className="mt-2 font-display text-xl font-bold text-text-primary">FastAPI</p>
              <p className="mt-1 text-xs text-text-secondary">Backend REST API</p>
            </div>
            <div className={`rounded-xl p-3 ${isLoading ? 'bg-navy-800' : isOperational ? 'bg-accent-teal/15' : 'bg-status-danger/15'}`}>
              {isLoading ? (
                <HeartPulse size={18} className="text-text-secondary" />
              ) : isOperational ? (
                <CheckCircle size={18} className="text-accent-teal" />
              ) : (
                <XCircle size={18} className="text-status-danger" />
              )}
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-navy-800">
            <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2 py-0.5 rounded ${
              isLoading ? 'bg-navy-800 text-text-secondary' : isOperational
                ? 'bg-accent-teal/10 text-accent-teal border border-accent-teal/20'
                : 'bg-status-danger/10 text-status-danger border border-status-danger/20'
            }`}>
              <span className={`h-1.5 w-1.5 rounded-full ${isLoading ? 'bg-text-secondary' : isOperational ? 'bg-accent-teal' : 'bg-status-danger'}`} />
              {isLoading ? 'Checking' : isOperational ? 'Operational' : 'Down'}
            </span>
          </div>
        </div>

        {/* Database */}
        <div className="card-dark p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-semibold tracking-widest text-text-secondary uppercase">Database</p>
              <p className="mt-2 font-display text-xl font-bold text-text-primary">PostgreSQL</p>
              <p className="mt-1 text-xs text-text-secondary">Primary data store</p>
            </div>
            <div className={`rounded-xl p-3 ${isLoading ? 'bg-navy-800' : dbOk ? 'bg-accent-teal/15' : 'bg-status-danger/15'}`}>
              <Database size={18} className={isLoading ? 'text-text-secondary' : dbOk ? 'text-accent-teal' : 'text-status-danger'} />
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-navy-800">
            <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2 py-0.5 rounded ${
              isLoading ? 'bg-navy-800 text-text-secondary' : dbOk
                ? 'bg-accent-teal/10 text-accent-teal border border-accent-teal/20'
                : 'bg-status-danger/10 text-status-danger border border-status-danger/20'
            }`}>
              <span className={`h-1.5 w-1.5 rounded-full ${isLoading ? 'bg-text-secondary' : dbOk ? 'bg-accent-teal' : 'bg-status-danger'}`} />
              {isLoading ? 'Checking' : dbOk ? 'Connected' : 'Error'}
            </span>
          </div>
        </div>

        {/* Version */}
        {health?.version && (
          <div className="card-dark p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold tracking-widest text-text-secondary uppercase">Backend Version</p>
                <p className="mt-2 font-display text-xl font-bold text-accent-blue font-mono">{health.version}</p>
                <p className="mt-1 text-xs text-text-secondary">Deployed build</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Raw response */}
      {health && (
        <div className="mt-6 card-dark p-5">
          <p className="text-xs font-semibold tracking-widest text-text-secondary uppercase mb-3">Raw Health Response</p>
          <pre className="font-mono text-xs text-accent-teal bg-navy-950 rounded-lg p-4 overflow-auto">
            {JSON.stringify(health, null, 2)}
          </pre>
        </div>
      )}
    </PageWrapper>
  )
}
