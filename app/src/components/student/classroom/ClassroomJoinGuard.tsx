import { useState } from 'react'
import { ShieldAlert, Loader2, ArrowRight, CheckCircle2, Lock } from 'lucide-react'
import { joinClassroom, getStudentProfile } from '@/api/auth'
import { useAuthStore } from '@/store/authStore'
import { useNotificationStore } from '@/store/notificationStore'

export const ClassroomJoinGuard = () => {
  const profile = useAuthStore((state) => state.profile)
  const setProfile = useAuthStore((state) => state.setProfile)
  const addNotification = useNotificationStore((state) => state.addNotification)

  const [classCode, setClassCode] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')
  const [forceShowInput, setForceShowInput] = useState(false)

  const handleJoin = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMsg('')
    const codeClean = classCode.trim().toUpperCase()
    if (!codeClean) return

    setIsSubmitting(true)
    try {
      const response = await joinClassroom(codeClean)
      addNotification({
        type: 'success',
        title: 'Join request sent!',
        message: response.message,
      })

      // Fetch fresh profile with pending state
      const freshProfile = await getStudentProfile()
      setProfile(freshProfile)
      setForceShowInput(false)
    } catch (err: any) {
      const errMsg = err?.response?.data?.detail || 'Failed to join classroom. Verify class code.'
      setErrorMsg(errMsg)
      addNotification({
        type: 'error',
        title: 'Failed to join',
        message: errMsg,
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const isPending = profile?.classroom_status === 'PENDING' && !forceShowInput
  const isRejected = profile?.classroom_status === 'REJECTED' && !forceShowInput

  if (isPending) {
    return (
      <div className="w-full max-w-md rounded-2xl border border-navy-800 bg-navy-900/60 p-6 text-center backdrop-blur-md shadow-2xl animate-fade-in">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-status-warning/15 text-status-warning animate-pulse">
          <Lock size={28} />
        </div>
        <h2 className="mt-5 font-display text-xl font-bold text-text-primary">
          Verification Pending
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-text-secondary">
          Your request to join the classroom{' '}
          <span className="font-semibold text-accent-blue">{profile?.classroom_name}</span> is pending review.
        </p>

        <div className="mt-5 rounded-lg bg-navy-950/60 p-4 text-left border border-navy-800">
          <div className="flex gap-2.5">
            <Loader2 className="mt-0.5 h-4 w-4 shrink-0 animate-spin text-status-warning" />
            <div>
              <p className="text-xs font-semibold text-text-primary">Awaiting Mentor Approval</p>
              <p className="mt-0.5 text-xs text-text-secondary leading-normal">
                Mentor <span className="font-medium text-text-primary">{profile?.mentor_name}</span> is currently reviewing your identity.
              </p>
            </div>
          </div>
        </div>

        <p className="mt-6 text-xs text-text-secondary/70 leading-relaxed">
          Need to change class code?{' '}
          <button
            onClick={() => setForceShowInput(true)}
            className="font-semibold text-accent-blue hover:text-accent-teal hover:underline transition-colors"
          >
            Enter new code
          </button>
        </p>
      </div>
    )
  }

  if (isRejected) {
    return (
      <div className="w-full max-w-md rounded-2xl border border-status-danger/30 bg-navy-900/60 p-6 text-center backdrop-blur-md shadow-2xl animate-fade-in">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-status-danger/15 text-status-danger">
          <ShieldAlert size={28} />
        </div>
        <h2 className="mt-5 font-display text-xl font-bold text-text-primary">
          Enrollment Rejected
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-text-secondary">
          Your request to join classroom{' '}
          <span className="font-semibold text-text-primary">{profile?.classroom_name}</span> was declined by the mentor.
        </p>

        <div className="mt-6 text-left">
          <button
            onClick={() => setForceShowInput(true)}
            className="btn-secondary w-full justify-center text-sm"
          >
            Try another Class Code
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full max-w-md rounded-2xl border border-navy-800 bg-navy-900/50 p-6 backdrop-blur-md shadow-glow animate-fade-in-up">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-accent-blue/15 text-accent-blue">
        <Lock size={22} />
      </div>
      <h2 className="font-display text-xl font-bold text-text-primary">
        Enter Class Code
      </h2>
      <p className="mt-2 text-sm text-text-secondary leading-relaxed">
        Please input the unique classroom code generated by your mentor to unlock your dashboard and start assignments.
      </p>

      <form onSubmit={handleJoin} className="mt-6 space-y-4">
        <div>
          <label htmlFor="class-code-input" className="mb-2 block text-xs font-semibold text-text-secondary uppercase tracking-wider">
            Class Code
          </label>
          <input
            id="class-code-input"
            type="text"
            required
            placeholder="CLASS-XXXXXX"
            className="input-dark font-mono uppercase tracking-widest text-center py-3 text-base"
            value={classCode}
            onChange={(e) => setClassCode(e.target.value)}
          />
          {errorMsg && (
            <p className="mt-2 text-xs text-status-danger leading-normal">{errorMsg}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={isSubmitting || !classCode.trim()}
          className="btn-primary w-full justify-center py-3 font-semibold"
        >
          {isSubmitting ? (
            <><Loader2 size={16} className="animate-spin" /> Verifying Code…</>
          ) : (
            <><CheckCircle2 size={16} /> Request Classroom Access <ArrowRight size={14} /></>
          )}
        </button>
      </form>
    </div>
  )
}
