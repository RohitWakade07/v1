import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { Eye, EyeOff, ShieldCheck, AlertCircle } from 'lucide-react'
import { loginAdmin } from '@/api/auth'
import { useAuthStore } from '@/store/authStore'
import { ThemeToggle } from '@/components/shared/ThemeToggle'

const schema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
})

type FormData = z.infer<typeof schema>

export const LoginPage = () => {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const [showPassword, setShowPassword] = useState(false)
  const [apiError, setApiError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema) })

  const onSubmit = async (data: FormData) => {
    setApiError(null)
    try {
      const res = await loginAdmin(data.username, data.password)
      setAuth(res.access_token, res.subject_id ?? data.username, res.role)
      navigate('/dashboard')
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: any } } })?.response?.data?.detail
      let errorMsg = 'Invalid credentials. Please try again.'
      if (typeof detail === 'string') {
        errorMsg = detail
      } else if (Array.isArray(detail)) {
        errorMsg = detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ')
      } else if (detail && typeof detail === 'object') {
        errorMsg = detail.message || JSON.stringify(detail)
      }
      setApiError(errorMsg)
    }
  }

  return (
    <div className="min-h-screen bg-navy-950 flex items-center justify-center p-4">
      {/* Theme toggle top-right */}
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>

      <div className="w-full max-w-sm animate-fade-in-up">
        {/* Logo + Branding */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="relative">
              <img
                src="/logo.png"
                alt="E-Yantra"
                className="h-16 w-16 rounded-2xl object-contain shadow-glow-teal"
              />
              <div className="absolute -bottom-1 -right-1 h-5 w-5 rounded-full bg-navy-900 border border-navy-800 flex items-center justify-center">
                <ShieldCheck size={11} className="text-accent-blue" />
              </div>
            </div>
          </div>
          <h1 className="font-display text-2xl font-bold text-text-primary">
            Admin Control Center
          </h1>
          <p className="text-sm text-text-secondary mt-1">E-Yantra EEP Secure Grading Platform</p>
        </div>

        {/* Card */}
        <div className="card-dark p-6">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* API error */}
            {apiError && (
              <div className="flex items-center gap-2 rounded-lg bg-status-danger/10 border border-status-danger/20 px-4 py-3">
                <AlertCircle size={15} className="text-status-danger shrink-0" />
                <p className="text-sm text-status-danger">{apiError}</p>
              </div>
            )}

            {/* Username */}
            <div>
              <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wide mb-1.5">
                Username
              </label>
              <input
                {...register('username')}
                type="text"
                autoComplete="username"
                className="input-dark"
                placeholder="admin_username"
              />
              {errors.username && (
                <p className="mt-1 text-xs text-status-danger">{errors.username.message}</p>
              )}
            </div>

            {/* Password */}
            <div>
              <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wide mb-1.5">
                Password
              </label>
              <div className="relative">
                <input
                  {...register('password')}
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  className="input-dark pr-10"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-secondary hover:text-text-primary"
                >
                  {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
              {errors.password && (
                <p className="mt-1 text-xs text-status-danger">{errors.password.message}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="btn-primary w-full justify-center mt-2"
            >
              {isSubmitting ? (
                <>
                  <span className="animate-spin-custom inline-block h-4 w-4 border-2 border-white/30 border-t-white rounded-full" />
                  Signing in…
                </>
              ) : (
                'Sign in to Admin Portal'
              )}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-text-secondary mt-6">
          Authorized personnel only. All actions are audited.
        </p>
      </div>
    </div>
  )
}
