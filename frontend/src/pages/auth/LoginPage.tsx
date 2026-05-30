import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { loginSchema } from '@/lib/schemas'
import { loginStudent } from '@/api/auth'
import { useAuthStore } from '@/store/authStore'
import { useNotificationStore } from '@/store/notificationStore'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { ShieldCheck, Eye, EyeOff, Loader2, GraduationCap, FlaskConical, Trophy } from 'lucide-react'

interface LoginFormValues {
  rollNumber: string
  password: string
}

const features = [
  { icon: GraduationCap, label: 'Seamless Access' },
  { icon: FlaskConical, label: 'Easy Submissions' },
  { icon: Trophy, label: 'Leaderboard & results' },
]

const LoginPage = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const setToken = useAuthStore((s) => s.setToken)
  const setProfile = useAuthStore((s) => s.setProfile)
  const addNotification = useNotificationStore((s) => s.addNotification)
  const [showPassword, setShowPassword] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({ resolver: zodResolver(loginSchema) })

  const onSubmit = handleSubmit(async (values) => {
    const response = await loginStudent({
      roll_number: values.rollNumber,
      password: values.password,
    })
    setToken(response.access_token)
    setProfile({
      roll_number: response.roll_number,
      student_uuid: response.student_uuid,
      role: 'student',
    })
    addNotification({
      type: 'success',
      title: 'Welcome back!',
      message: 'You are signed in successfully.',
    })
    const params = new URLSearchParams(location.search)
    navigate(params.get('redirect') || '/')
  })

  return (
    <div className="flex min-h-screen bg-navy-950">
      {/* ── Left panel — branding ─────────────────────────────── */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-between p-12 relative overflow-hidden"
        style={{ background: 'linear-gradient(145deg, #edf1f5ff 0%, #f5f7f9ff 50%, #f5f7f9ff 100%)' }}>
        {/* Background decorations */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-20 left-10 h-48 w-48 rounded-full bg-accent-blue/5 blur-3xl" />
          <div className="absolute bottom-32 right-10 h-64 w-64 rounded-full bg-accent-teal/5 blur-3xl" />
        </div>

        {/* Logo */}
        <div className="relative flex items-center gap-3">
          <img src="/logo.png" alt="Logo" className="h-10 w-10 object-contain rounded-xl shadow-glow" />
          <div>
            <p className="font-display text-base font-bold text-text-primary">E-Yantra EEP</p>
            <p className="text-xs text-text-secondary">Academic Evaluation Platform</p>
          </div>
        </div>

        {/* Hero text */}
        <div className="relative space-y-6">
          <div>
            <h1 className="font-display text-4xl font-bold leading-tight">
              <span className="text-text-primary">Your Journey </span>
              <br />
              <span className="gradient-text">from Beginner to Builder</span>
              <br />
              <span className="text-text-primary">Starts Here.</span>
            </h1>
           
          </div>

          <div className="space-y-3">
            {features.map(({ icon: Icon, label }) => (
              <div key={label} className="flex items-center gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-navy-800/60">
                  <Icon size={15} className="text-accent-teal" />
                </div>
                <span className="text-sm text-text-secondary">{label}</span>
              </div>
            ))}
          </div>
        </div>

        <p className="relative text-xs text-text-secondary/60">
          Phase 1 MVP · EYSIP Secure Academic Grading Platform
        </p>
      </div>

      {/* ── Right panel — form ────────────────────────────────── */}
      <div className="flex flex-1 items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm animate-fade-in-up">
          {/* Mobile logo */}
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <img src="/logo.png" alt="Logo" className="h-8 w-8 object-contain rounded-lg" />
            <span className="font-display text-sm font-bold text-text-primary">E-Yantra EEP</span>
          </div>

          <h2 className="font-display text-2xl font-bold text-text-primary">Sign in</h2>
          <p className="mt-1 text-sm text-text-secondary">
            Enter your roll number and password to continue.
          </p>

          <form className="mt-8 space-y-5" onSubmit={onSubmit} noValidate>
            {/* Roll Number */}
            <div>
              <label htmlFor="login-roll" className="mb-1.5 block text-sm font-medium text-text-secondary">
                Roll Number
              </label>
              <input
                id="login-roll"
                type="text"
                autoComplete="username"
                placeholder="e.g. 2024CSE001"
                className="input-dark"
                aria-describedby={errors.rollNumber ? 'login-roll-error' : undefined}
                {...register('rollNumber')}
              />
              {errors.rollNumber && (
                <p id="login-roll-error" className="mt-1.5 text-xs text-status-danger">
                  {errors.rollNumber.message}
                </p>
              )}
            </div>

            {/* Password */}
            <div>
              <label htmlFor="login-password" className="mb-1.5 block text-sm font-medium text-text-secondary">
                Password
              </label>
              <div className="relative">
                <input
                  id="login-password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  placeholder="••••••••"
                  className="input-dark pr-10"
                  aria-describedby={errors.password ? 'login-password-error' : undefined}
                  {...register('password')}
                />
                <button
                  type="button"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-secondary hover:text-text-primary transition-colors"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {errors.password && (
                <p id="login-password-error" className="mt-1.5 text-xs text-status-danger">
                  {errors.password.message}
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="btn-primary w-full justify-center py-2.5"
            >
              {isSubmitting ? (
                <>
                  <Loader2 size={16} className="animate-spin" /> Signing in…
                </>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-text-secondary">
            Don't have an account?{' '}
            <Link to="/register" className="font-medium text-accent-blue hover:text-accent-teal transition-colors">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default LoginPage
