import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Loader2 } from 'lucide-react'
import { mentorLoginSchema } from '@/lib/schemas'
import { useAuth } from '@/hooks/useAuth'

type LoginFormValues = z.infer<typeof mentorLoginSchema>

export const LoginPage = () => {
  const loginMutation = useAuth()
  
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(mentorLoginSchema),
    defaultValues: {
      username: '',
      password: '',
    },
  })

  const onSubmit = (data: LoginFormValues) => {
    loginMutation.mutate(data)
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-navy-950 p-4">
      <div className="w-full max-w-md animate-fade-in-up">
        <div className="mb-8 text-center">
          <img src="/logo.png" alt="Logo" className="mx-auto mb-4 h-16 w-16 object-contain rounded-2xl shadow-glow-teal" />
          <h1 className="font-display text-3xl font-bold text-text-primary">Mentor Portal</h1>
          <p className="mt-2 text-text-secondary">Sign in to manage the grading platform</p>
        </div>

        <div className="rounded-2xl border border-navy-800 bg-navy-900/50 p-8 shadow-card backdrop-blur-sm">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-text-primary" htmlFor="username">
                Username
              </label>
              <input
                id="username"
                type="text"
                className="input-dark"
                placeholder="Enter your username"
                {...register('username')}
              />
              {errors.username && (
                <p className="mt-1.5 text-xs text-status-danger">{errors.username.message}</p>
              )}
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-text-primary" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                className="input-dark"
                placeholder="••••••••"
                {...register('password')}
              />
              {errors.password && (
                <p className="mt-1.5 text-xs text-status-danger">{errors.password.message}</p>
              )}
            </div>

            <button
              type="submit"
              className="btn-primary w-full bg-accent-teal hover:bg-[#159e82] focus-visible:ring-accent-teal/60"
              disabled={loginMutation.isPending}
            >
              {loginMutation.isPending ? (
                <Loader2 size={18} className="animate-spin" />
              ) : (
                'Sign In'
              )}
            </button>
          </form>
        </div>

        <div className="mt-8 text-center text-sm text-text-secondary">
          <p>Secure Academic Grading Platform &copy; {new Date().getFullYear()}</p>
        </div>
      </div>
    </div>
  )
}

export default LoginPage
