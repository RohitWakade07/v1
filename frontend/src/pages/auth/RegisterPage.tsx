import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { registerSchema } from '@/lib/schemas'
import { registerStudent, loginStudent, getStudentProfile } from '@/api/auth'
import { useAuthStore } from '@/store/authStore'
import { useNotificationStore } from '@/store/notificationStore'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Loader2 } from 'lucide-react'
import { ThemeToggle } from '@/components/shared/ThemeToggle'

interface RegisterFormValues {
  fullName: string
  email: string
  rollNumber: string
  password: string
  classCode: string
}

const RegisterPage = () => {
  const navigate = useNavigate()
  const loginStudentStore = useAuthStore((s) => s.loginStudent)
  const addNotification = useNotificationStore((s) => s.addNotification)
  const [showPassword, setShowPassword] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>({ resolver: zodResolver(registerSchema) })

  const onSubmit = handleSubmit(async (values) => {
    // 1. Register the student
    await registerStudent({
      full_name: values.fullName,
      email: values.email,
      roll_number: values.rollNumber,
      password: values.password,
      class_code: values.classCode,
    })

    // 2. Automatically log in to obtain the access token
    const loginResponse = await loginStudent(values.rollNumber, values.password)

    // Save token to auth store temporarily to authorize getStudentProfile
    useAuthStore.setState({ token: loginResponse.access_token })

    // 3. Fetch the complete profile details
    let profileData = {
      roll_number: loginResponse.roll_number,
      student_uuid: loginResponse.student_uuid,
      role: 'student' as const,
    }

    try {
      const fetchedProfile = await getStudentProfile()
      profileData = { ...profileData, ...fetchedProfile }
    } catch (error) {
      console.error('Failed to fetch student profile after registration:', error)
    }

    loginStudentStore(loginResponse.access_token, profileData)

    addNotification({
      type: 'success',
      title: 'Account created!',
      message: 'Welcome to the E-Yantra EEP Platform.',
    })
    navigate('/')
  })

  return (
    <div className="flex min-h-screen bg-navy-950">
      {/* ── Left branding panel ───────────────────────────────── */}
      <div className="auth-brand-panel hidden lg:flex lg:w-1/2 flex-col justify-between p-12 relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-20 right-10 h-48 w-48 rounded-full bg-accent-teal/5 blur-3xl" />
          <div className="absolute bottom-32 left-10 h-64 w-64 rounded-full bg-accent-blue/5 blur-3xl" />
        </div>

        <div className="relative flex items-center gap-3">
          <img src="/logo.png" alt="Logo" className="h-10 w-10 object-contain rounded-xl shadow-glow" />
          <div>
            <p className="font-display text-base font-bold text-text-primary">E-Yantra EEP</p>
            <p className="text-xs text-text-secondary">Academic Evaluation Platform</p>
          </div>
        </div>

        <div className="relative space-y-4">
          <h1 className="font-display text-4xl font-bold leading-tight">
            <span className="text-text-primary">Start your</span>
            <br />
            <span className="gradient-text">journey</span>
            <br />
            <span className="text-text-primary">today.</span>
          </h1>
          <p className="text-sm leading-relaxed text-text-secondary max-w-sm">
            Create your student account and get immediate access to assignments .
          </p>
          
        </div>

        <p className="relative text-xs text-text-secondary/60">
          Phase 1 MVP · Academic Grading Platform
        </p>
      </div>

      {/* ── Right form panel ──────────────────────────────────── */}
      <div className="relative flex flex-1 items-center justify-center px-6 py-12">
        <div className="absolute top-6 right-6 z-10">
          <ThemeToggle />
        </div>
        <div className="w-full max-w-sm animate-fade-in-up">
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <img src="/logo.png" alt="Logo" className="h-8 w-8 object-contain rounded-lg" />
            <span className="font-display text-sm font-bold text-text-primary">E-Yantra EEP</span>
          </div>

          <h2 className="font-display text-2xl font-bold text-text-primary">Create account</h2>
          <p className="mt-1 text-sm text-text-secondary">
            Fill in your details to get started.
          </p>

          <form className="auth-form-card mt-8 space-y-4 p-8" onSubmit={onSubmit} noValidate>
            {/* Full Name */}
            <div>
              <label htmlFor="reg-name" className="mb-1.5 block text-sm font-medium text-text-secondary">
                Full Name
              </label>
              <input
                id="reg-name"
                type="text"
                autoComplete="name"
                placeholder="Your full name"
                className="input-dark auth-input"
                {...register('fullName')}
              />
              {errors.fullName && (
                <p className="mt-1.5 text-xs text-status-danger">{errors.fullName.message}</p>
              )}
            </div>

            {/* Email */}
            <div>
              <label htmlFor="reg-email" className="mb-1.5 block text-sm font-medium text-text-secondary">
                Email
              </label>
              <input
                id="reg-email"
                type="email"
                autoComplete="email"
                placeholder="you@university.edu"
                className="input-dark auth-input"
                {...register('email')}
              />
              {errors.email && (
                <p className="mt-1.5 text-xs text-status-danger">{errors.email.message}</p>
              )}
            </div>

            {/* Roll Number */}
            <div>
              <label htmlFor="reg-roll" className="mb-1.5 block text-sm font-medium text-text-secondary">
                Roll Number
              </label>
              <input
                id="reg-roll"
                type="text"
                autoComplete="username"
                placeholder="e.g. 2024CSE001"
                className="input-dark auth-input"
                {...register('rollNumber')}
              />
              {errors.rollNumber && (
                <p className="mt-1.5 text-xs text-status-danger">{errors.rollNumber.message}</p>
              )}
            </div>

            {/* Class Code */}
            <div>
              <label htmlFor="reg-classcode" className="mb-1.5 block text-sm font-medium text-text-secondary">
                Class Code (provided by your Mentor)
              </label>
              <input
                id="reg-classcode"
                type="text"
                placeholder="e.g. CLASS-A79B2D"
                className="input-dark auth-input font-mono uppercase"
                {...register('classCode')}
              />
              {errors.classCode && (
                <p className="mt-1.5 text-xs text-status-danger">{errors.classCode.message}</p>
              )}
            </div>

            {/* Password */}
            <div>
              <label htmlFor="reg-password" className="mb-1.5 block text-sm font-medium text-text-secondary">
                Password
              </label>
              <div className="relative">
                <input
                  id="reg-password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  placeholder="Min. 6 characters"
                  className="input-dark auth-input pr-10"
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
                <p className="mt-1.5 text-xs text-status-danger">{errors.password.message}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="btn-primary w-full justify-center py-2.5"
            >
              {isSubmitting ? (
                <><Loader2 size={16} className="animate-spin" /> Creating account…</>
              ) : (
                'Create Account'
              )}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-text-secondary">
            Already have an account?{' '}
            <Link to="/login" className="font-medium text-accent-blue hover:text-accent-teal transition-colors">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default RegisterPage
