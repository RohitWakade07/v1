import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { loginStudent, loginStaff, getStudentProfile } from '@/api/auth'
import { useAuthStore } from '@/store/authStore'
import { useNotificationStore } from '@/store/notificationStore'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Loader2, GraduationCap, FlaskConical, Trophy, UserCheck, ShieldAlert } from 'lucide-react'
import { ThemeToggle } from '@/components/shared/ThemeToggle'

// Schemas for forms
const studentFormSchema = z.object({
  rollNumber: z.string().min(3, 'Roll number is required'),
  password: z.string().min(6, 'Password is required'),
})

const staffFormSchema = z.object({
  username: z.string().min(2, 'Username is required'),
  password: z.string().min(6, 'Password is required'),
})

type StudentFormValues = z.infer<typeof studentFormSchema>
type StaffFormValues = z.infer<typeof staffFormSchema>

const features = [
  { icon: GraduationCap, label: 'Student Coursework & Submissions' },
  { icon: FlaskConical, label: 'Mentor Evaluator & Sandbox' },
  { icon: Trophy, label: 'Platform Performance & Grades' },
]

export const LoginPage = () => {
  const navigate = useNavigate()
  const location = useLocation()

  const loginStoreStudent = useAuthStore((s) => s.loginStudent)
  const loginStoreStaff = useAuthStore((s) => s.loginStaff)
  const addNotification = useNotificationStore((s) => s.addNotification)

  const [activeTab, setActiveTab] = useState<'student' | 'staff'>('student')
  const [showPassword, setShowPassword] = useState(false)

  // React hook form for Student
  const {
    register: registerStudentForm,
    handleSubmit: handleStudentSubmit,
    formState: { errors: studentErrors, isSubmitting: isStudentSubmitting },
  } = useForm<StudentFormValues>({
    resolver: zodResolver(studentFormSchema),
    defaultValues: { rollNumber: '', password: '' },
  })

  // React hook form for Staff
  const {
    register: registerStaffForm,
    handleSubmit: handleStaffSubmit,
    formState: { errors: staffErrors, isSubmitting: isStaffSubmitting },
  } = useForm<StaffFormValues>({
    resolver: zodResolver(staffFormSchema),
    defaultValues: { username: '', password: '' },
  })

  // Submit Handler for Student
  const onStudentSubmit = handleStudentSubmit(async (values) => {
    try {
      const response = await loginStudent(values.rollNumber, values.password)
      // Temporarily set token in Zustand state to authorize getStudentProfile
      useAuthStore.setState({ token: response.access_token })

      let profileData = {
        roll_number: response.roll_number,
        student_uuid: response.student_uuid,
        role: 'student' as const,
      }

      try {
        const fetchedProfile = await getStudentProfile()
        profileData = { ...profileData, ...fetchedProfile }
      } catch (error) {
        console.error('Failed to fetch student profile details:', error)
      }

      loginStoreStudent(response.access_token, profileData)

      addNotification({
        type: 'success',
        title: 'Welcome back!',
        message: 'You are signed in as a Student.',
      })

      const params = new URLSearchParams(location.search)
      navigate(params.get('redirect') || '/student')
    } catch (err: any) {
      console.error(err)
      // Error notifications are already handled by the axios instance response interceptor
    }
  })

  // Submit Handler for Staff
  const onStaffSubmit = handleStaffSubmit(async (values) => {
    try {
      const response = await loginStaff(values)
      const role = response.role as 'mentor' | 'admin'

      loginStoreStaff(
        response.access_token,
        role,
        values.username,
        response.subject_id ?? '',
        response.mentor_uuid ?? response.subject_id ?? undefined
      )

      addNotification({
        type: 'success',
        title: 'Welcome back!',
        message: `Signed in successfully as ${role === 'admin' ? 'Admin' : 'Mentor'}.`,
      })

      const params = new URLSearchParams(location.search)
      const redirect = params.get('redirect')
      if (redirect) {
        navigate(redirect)
      } else {
        navigate(role === 'admin' ? '/admin' : '/mentor')
      }
    } catch (err: any) {
      console.error(err)
    }
  })

  return (
    <div className="flex min-h-screen bg-navy-950">
      {/* ── Left panel — branding ─────────────────────────────── */}
      <div className="auth-brand-panel hidden lg:flex lg:w-1/2 flex-col justify-between p-12 relative overflow-hidden">
        {/* Background decorations */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-20 left-10 h-48 w-48 rounded-full bg-accent-blue/10 blur-3xl" />
          <div className="absolute bottom-32 right-10 h-64 w-64 rounded-full bg-accent-teal/10 blur-3xl" />
        </div>

        {/* Logo */}
        <div className="relative flex items-center gap-3">
          <img src="/logo.png" alt="Logo" className="h-10 w-10 object-contain rounded-xl shadow-glow-teal bg-navy-900/80 p-1" />
          <div>
            <p className="font-display text-base font-bold text-text-primary">E-Yantra EEP</p>
            <p className="text-xs text-text-secondary">Academic Evaluation Platform</p>
          </div>
        </div>

        {/* Hero text */}
        <div className="relative space-y-6">
          <div>
            <h1 className="font-display text-4xl font-bold leading-tight text-text-primary">
              Unified Academic
              <br />
              <span className="gradient-text font-extrabold bg-gradient-to-r from-accent-blue to-accent-teal bg-clip-text text-transparent">Grading & Evaluation</span>
              <br />
              Platform.
            </h1>
          </div>

          <div className="space-y-4">
            {features.map(({ icon: Icon, label }) => (
              <div key={label} className="flex items-center gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-navy-800/60 border border-navy-700/50">
                  <Icon size={15} className="text-accent-teal" />
                </div>
                <span className="text-sm text-text-secondary">{label}</span>
              </div>
            ))}
          </div>
        </div>

        <p className="relative text-xs text-text-secondary/40">
          EEP Consolidation · Secure Role-Based Portals
        </p>
      </div>

      {/* ── Right panel — form ────────────────────────────────── */}
      <div className="relative flex flex-1 items-center justify-center px-6 py-12">
        <div className="absolute top-6 right-6 z-10">
          <ThemeToggle />
        </div>
        <div className="w-full max-w-md animate-fade-in-up">
          {/* Mobile logo */}
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <img src="/logo.png" alt="Logo" className="h-8 w-8 object-contain rounded-lg" />
            <span className="font-display text-sm font-bold text-text-primary">E-Yantra EEP</span>
          </div>

          <h2 className="font-display text-2xl font-bold text-text-primary">Sign in</h2>
          <p className="mt-1 text-sm text-text-secondary mb-6">
            Choose your portal role and enter credentials.
          </p>

          {/* Role Tabs */}
          <div className="auth-tab-shell flex rounded-xl p-1 mb-6">
            <button
              onClick={() => setActiveTab('student')}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium rounded-lg transition-all ${activeTab === 'student'
                  ? 'auth-tab-active text-accent-blue'
                  : 'text-text-secondary hover:text-text-primary hover:bg-navy-800/30'
                }`}
            >
              <GraduationCap size={16} />
              Student Portal
            </button>
            <button
              onClick={() => setActiveTab('staff')}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium rounded-lg transition-all ${activeTab === 'staff'
                  ? 'auth-tab-active text-accent-teal'
                  : 'text-text-secondary hover:text-text-primary hover:bg-navy-800/30'
                }`}
            >
              <UserCheck size={16} />
              Staff / Admin
            </button>
          </div>

          {/* Form container */}
          <div className="auth-form-card p-8">
            {activeTab === 'student' ? (
              <form onSubmit={onStudentSubmit} className="space-y-5" noValidate>
                {/* Student Roll Number */}
                <div>
                  <label htmlFor="login-roll" className="mb-1.5 block text-sm font-medium text-text-secondary">
                    Roll Number
                  </label>
                  <input
                    id="login-roll"
                    type="text"
                    autoComplete="username"
                    placeholder="e.g. 2024CSE001"
                    className="input-dark auth-input w-full focus:border-accent-blue"
                    aria-describedby={studentErrors.rollNumber ? 'login-roll-error' : undefined}
                    {...registerStudentForm('rollNumber')}
                  />
                  {studentErrors.rollNumber && (
                    <p id="login-roll-error" className="mt-1.5 text-xs text-status-danger">
                      {studentErrors.rollNumber.message}
                    </p>
                  )}
                </div>

                {/* Student Password */}
                <div>
                  <label htmlFor="login-password-student" className="mb-1.5 block text-sm font-medium text-text-secondary">
                    Password
                  </label>
                  <div className="relative">
                    <input
                      id="login-password-student"
                      type={showPassword ? 'text' : 'password'}
                      autoComplete="current-password"
                      placeholder="••••••••"
                      className="input-dark auth-input w-full pr-10 focus:border-accent-blue"
                      aria-describedby={studentErrors.password ? 'login-password-student-error' : undefined}
                      {...registerStudentForm('password')}
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
                  {studentErrors.password && (
                    <p id="login-password-student-error" className="mt-1.5 text-xs text-status-danger">
                      {studentErrors.password.message}
                    </p>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={isStudentSubmitting}
                  className="btn-primary w-full flex items-center justify-center gap-2 py-2.5 rounded-xl font-medium bg-accent-blue hover:bg-[#2471A3] text-white transition-all shadow-glow"
                >
                  {isStudentSubmitting ? (
                    <>
                      <Loader2 size={16} className="animate-spin" /> Signing in…
                    </>
                  ) : (
                    'Sign In to Student Portal'
                  )}
                </button>
              </form>
            ) : (
              <form onSubmit={onStaffSubmit} className="space-y-5" noValidate>
                {/* Staff Username */}
                <div>
                  <label htmlFor="login-username" className="mb-1.5 block text-sm font-medium text-text-secondary">
                    Username
                  </label>
                  <input
                    id="login-username"
                    type="text"
                    autoComplete="username"
                    placeholder="Enter your username"
                    className="input-dark auth-input w-full focus:border-accent-teal"
                    aria-describedby={staffErrors.username ? 'login-username-error' : undefined}
                    {...registerStaffForm('username')}
                  />
                  {staffErrors.username && (
                    <p id="login-username-error" className="mt-1.5 text-xs text-status-danger">
                      {staffErrors.username.message}
                    </p>
                  )}
                </div>

                {/* Staff Password */}
                <div>
                  <label htmlFor="login-password-staff" className="mb-1.5 block text-sm font-medium text-text-secondary">
                    Password
                  </label>
                  <div className="relative">
                    <input
                      id="login-password-staff"
                      type={showPassword ? 'text' : 'password'}
                      autoComplete="current-password"
                      placeholder="••••••••"
                      className="input-dark auth-input w-full pr-10 focus:border-accent-teal"
                      aria-describedby={staffErrors.password ? 'login-password-staff-error' : undefined}
                      {...registerStaffForm('password')}
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
                  {staffErrors.password && (
                    <p id="login-password-staff-error" className="mt-1.5 text-xs text-status-danger">
                      {staffErrors.password.message}
                    </p>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={isStaffSubmitting}
                  className="btn-primary w-full flex items-center justify-center gap-2 py-2.5 rounded-xl font-medium bg-accent-teal hover:bg-[#159e82] text-white transition-all shadow-glow-teal"
                >
                  {isStaffSubmitting ? (
                    <>
                      <Loader2 size={16} className="animate-spin" /> Signing in…
                    </>
                  ) : (
                    'Sign In to Staff Portal'
                  )}
                </button>
              </form>
            )}
          </div>

          {activeTab === 'student' && (
            <p className="mt-6 text-center text-sm text-text-secondary">
              Don't have a student account?{' '}
              <Link to="/register" className="font-medium text-accent-blue hover:text-accent-teal transition-colors">
                Create one
              </Link>
            </p>
          )}

          {activeTab === 'staff' && (
            <div className="auth-notice mt-6 flex gap-2 items-start justify-center p-3 rounded-xl">
              <ShieldAlert size={16} className="text-accent-teal shrink-0 mt-0.5" />
              <p className="text-xs text-text-secondary text-center">
                Staff accounts must be created by an administrator.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default LoginPage
