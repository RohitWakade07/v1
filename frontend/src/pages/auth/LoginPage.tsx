import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { loginSchema } from '@/lib/schemas'
import { loginStudent } from '@/api/auth'
import { useAuthStore } from '@/store/authStore'
import { useNotificationStore } from '@/store/notificationStore'
import { Link, useLocation, useNavigate } from 'react-router-dom'

interface LoginFormValues {
  rollNumber: string
  password: string
}

const LoginPage = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const setToken = useAuthStore((state) => state.setToken)
  const setProfile = useAuthStore((state) => state.setProfile)
  const addNotification = useNotificationStore((state) => state.addNotification)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  })

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
      title: 'Welcome back',
      message: 'You are signed in successfully.',
    })
    const params = new URLSearchParams(location.search)
    const redirect = params.get('redirect') || '/'
    navigate(redirect)
  })

  return (
    <div className="flex min-h-screen items-center justify-center bg-navy-950 px-4">
      <div className="w-full max-w-md rounded-xl border border-navy-800 bg-navy-900/50 p-8 shadow-card">
        <h1 className="font-display text-2xl font-semibold text-text-primary">
          Student Login
        </h1>
        <p className="mt-2 text-sm text-text-secondary">
          Sign in with your roll number and password.
        </p>
        <form className="mt-6 space-y-4" onSubmit={onSubmit}>
          <div>
            <label className="text-sm text-text-secondary">Roll Number</label>
            <input
              type="text"
              className="mt-1 w-full rounded-lg border border-navy-800 bg-navy-950 px-3 py-2 text-text-primary"
              {...register('rollNumber')}
            />
            {errors.rollNumber && (
              <p className="mt-1 text-xs text-status-danger">
                {errors.rollNumber.message}
              </p>
            )}
          </div>
          <div>
            <label className="text-sm text-text-secondary">Password</label>
            <input
              type="password"
              className="mt-1 w-full rounded-lg border border-navy-800 bg-navy-950 px-3 py-2 text-text-primary"
              {...register('password')}
            />
            {errors.password && (
              <p className="mt-1 text-xs text-status-danger">
                {errors.password.message}
              </p>
            )}
          </div>
          <button
            type="submit"
            className="w-full rounded-lg bg-accent-blue px-4 py-2 text-sm font-medium text-white"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        <p className="mt-4 text-sm text-text-secondary">
          New here?{' '}
          <Link className="text-accent-blue" to="/register">
            Create an account
          </Link>
        </p>
      </div>
    </div>
  )
}

export default LoginPage
