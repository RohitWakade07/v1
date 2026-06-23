import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { PageWrapper } from '@/components/shared/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { useAuthStore } from '@/store/authStore'
import { useNotificationStore } from '@/store/notificationStore'
import { passwordChangeSchema } from '@/lib/schemas'
import { changeStudentPassword } from '@/api/auth'

interface PasswordFormValues {
  currentPassword: string
  newPassword: string
  confirmPassword: string
}

const ProfilePage = () => {
  const profile = useAuthStore((state) => state.profile)
  const addNotification = useNotificationStore((state) => state.addNotification)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<PasswordFormValues>({
    resolver: zodResolver(passwordChangeSchema),
  })

  const onSubmit = handleSubmit(async (values) => {
    try {
      await changeStudentPassword(values.currentPassword, values.newPassword)
      addNotification({ type: 'success', title: 'Success', message: 'Password changed successfully' })
      reset()
    } catch (error: any) {
      const msg = error?.response?.data?.detail?.message || 'Failed to change password'
      addNotification({ type: 'error', title: 'Error', message: msg })
    }
  })

  return (
    <PageWrapper>
      <PageHeader
        title="Profile"
        description="Review your account information and update credentials."
      />
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-navy-800 bg-navy-900/50 p-6 shadow-card">
          <h3 className="font-display text-lg font-semibold text-text-primary">
            Student Details
          </h3>
          <div className="mt-4 space-y-3 text-sm text-text-secondary">
            <div>
              <p className="text-xs uppercase">Full Name</p>
              <p className="text-text-primary">
                {profile?.full_name || 'Not provided'}
              </p>
            </div>
            <div>
              <p className="text-xs uppercase">Roll Number</p>
              <p className="text-text-primary">
                {profile?.roll_number || 'N/A'}
              </p>
            </div>
            <div>
              <p className="text-xs uppercase">Email</p>
              <p className="text-text-primary">{profile?.email || 'N/A'}</p>
            </div>
          </div>
        </div>
        <div className="rounded-xl border border-navy-800 bg-navy-900/50 p-6 shadow-card">
          <h3 className="font-display text-lg font-semibold text-text-primary">
            Change Password
          </h3>
          <form className="mt-4 space-y-3" onSubmit={onSubmit}>
            <div>
              <label className="text-sm text-text-secondary">Current Password</label>
              <input
                type="password"
                className="mt-1 w-full rounded-lg border border-navy-800 bg-navy-950 px-3 py-2 text-text-primary"
                {...register('currentPassword')}
              />
              {errors.currentPassword && (
                <p className="mt-1 text-xs text-status-danger">
                  {errors.currentPassword.message}
                </p>
              )}
            </div>
            <div>
              <label className="text-sm text-text-secondary">New Password</label>
              <input
                type="password"
                className="mt-1 w-full rounded-lg border border-navy-800 bg-navy-950 px-3 py-2 text-text-primary"
                {...register('newPassword')}
              />
              {errors.newPassword && (
                <p className="mt-1 text-xs text-status-danger">
                  {errors.newPassword.message}
                </p>
              )}
            </div>
            <div>
              <label className="text-sm text-text-secondary">Confirm Password</label>
              <input
                type="password"
                className="mt-1 w-full rounded-lg border border-navy-800 bg-navy-950 px-3 py-2 text-text-primary"
                {...register('confirmPassword')}
              />
              {errors.confirmPassword && (
                <p className="mt-1 text-xs text-status-danger">
                  {errors.confirmPassword.message}
                </p>
              )}
            </div>
            <button
              type="submit"
              className="rounded-lg bg-accent-blue px-4 py-2 text-sm font-medium text-white"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Updating...' : 'Update Password'}
            </button>
          </form>
        </div>
      </div>
    </PageWrapper>
  )
}

export default ProfilePage
