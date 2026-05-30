import { Link } from 'react-router-dom'
import { ShieldAlert } from 'lucide-react'

export const NotFoundPage = () => (
  <div className="flex min-h-screen items-center justify-center bg-navy-950">
    <div className="text-center animate-fade-in-up">
      <div className="flex justify-center mb-4">
        <div className="rounded-2xl bg-navy-900 border border-navy-800 p-5">
          <ShieldAlert size={48} className="text-accent-blue" />
        </div>
      </div>
      <h1 className="font-display text-4xl font-bold text-text-primary">404</h1>
      <p className="mt-2 text-text-secondary">This page doesn't exist in the Admin Control Center.</p>
      <Link to="/dashboard" className="btn-primary mt-6 inline-flex">
        Back to Dashboard
      </Link>
    </div>
  </div>
)
