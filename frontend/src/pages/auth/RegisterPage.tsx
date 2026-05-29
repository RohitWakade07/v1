import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { registerSchema } from '@/lib/schemas'
import { registerStudent } from '@/api/auth'
import { useAuthStore } from '@/store/authStore'
import { useNotificationStore } from '@/store/notificationStore'
import { Link, useNavigate } from 'react-router-dom'

interface RegisterFormValues {
  fullName: string
  email: string
  rollNumber: string
  password: string
}

const RegisterPage = () => {
  const navigate = useNavigate()
  const setToken = useAuthStore((state) => state.setToken)
  const setProfile = useAuthStore((state) => state.setProfile)
  const addNotification = useNotificationStore((state) => state.addNotification)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
  })

  const onSubmit = handleSubmit(async (values) => {
    const response = await registerStudent({
      full_name: values.fullName,
      email: values.email,
      roll_number: values.rollNumber,
      password: values.password,
    })
    setToken(response.access_token)
    setProfile({
      roll_number: response.roll_number,
      student_uuid: response.student_uuid,
      role: 'student',
      email: values.email,
      full_name: values.fullName,
    })
    addNotification({
      type: 'success',
      title: 'Registration complete',
      message: 'Your student account has been created.',
    })
    navigate('/')
  })

  return (
    <div className="flex min-h-screen items-center justify-center bg-navy-950 px-4">
      <div className="w-full max-w-md rounded-xl border border-navy-800 bg-navy-900/50 p-8 shadow-card">
        <h1 className="font-display text-2xl font-semibold text-text-primary">
          Student Registration
        </h1>
        <p className="mt-2 text-sm text-text-secondary">
          Create your student profile to access assignments.
        </p>
        <form className="mt-6 space-y-4" onSubmit={onSubmit}>
          <div>
            <label className="text-sm text-text-secondary">Full Name</label>
            <input
              type="text"
              className="mt-1 w-full rounded-lg border border-navy-800 bg-navy-950 px-3 py-2 text-text-primary"
              {...register('fullName')}
            />
            {errors.fullName && (
              <p className="mt-1 text-xs text-status-danger">
                {errors.fullName.message}
              </p>
            )}
          </div>
          <div>
            <label className="text-sm text-text-secondary">Email</label>
            <input
              type="email"
              className="mt-1 w-full rounded-lg border border-navy-800 bg-navy-950 px-3 py-2 text-text-primary"
              {...register('email')}
            />
            {errors.email && (
              <p className="mt-1 text-xs text-status-danger">
                {errors.email.message}
              </p>
            )}
          </div>
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
            {isSubmitting ? 'Creating account...' : 'Create Account'}
          </button>
        </form>
        <p className="mt-4 text-sm text-text-secondary">
          Already have an account?{' '}
          <Link className="text-accent-blue" to="/login">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}

export default RegisterPage
