import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Lock, CheckCircle, XCircle, AlertTriangle, Loader2, Trophy, ChevronLeft } from 'lucide-react'
import {
  getStudentQuiz,
  getStudentQuizQuestions,
  submitQuizAttempt,
  getQuizResult,
  type QuizPublic,
  type QuizQuestion,
  type QuizAttemptResult,
} from '@/api/student/quiz'

export const QuizPage = () => {
  const { assignmentId } = useParams<{ assignmentId: string }>()
  const navigate = useNavigate()

  const [quiz, setQuiz] = useState<QuizPublic | null>(null)
  const [questions, setQuestions] = useState<QuizQuestion[]>([])
  const [result, setResult] = useState<QuizAttemptResult | null>(null)
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string[]>>({})
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [quizLocked, setQuizLocked] = useState(false)
  const [unansweredIds, setUnansweredIds] = useState<Set<string>>(new Set())

  useEffect(() => {
    if (!assignmentId) return
    const load = async () => {
      setLoading(true)
      try {
        const q = await getStudentQuiz(assignmentId)
        setQuiz(q)
        // Try to get existing result
        try {
          const existing = await getQuizResult(q.id)
          setResult(existing)
          return
        } catch {
          // Not attempted yet, load questions
        }
        const qs = await getStudentQuizQuestions(q.id)
        setQuestions(qs)
      } catch (err: any) {
        const code = err?.response?.data?.detail?.error
        if (code === 'QUIZ_LOCKED') setQuizLocked(true)
        else setError(err?.response?.data?.detail?.message || 'Failed to load quiz')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [assignmentId])

  const toggleOption = (questionId: string, optionId: string, isSingle: boolean) => {
    setSelectedAnswers(prev => {
      const current = prev[questionId] || []
      if (isSingle) {
        return { ...prev, [questionId]: [optionId] }
      }
      const exists = current.includes(optionId)
      return {
        ...prev,
        [questionId]: exists ? current.filter(id => id !== optionId) : [...current, optionId],
      }
    })
  }

  const handleSubmit = async () => {
    if (!quiz) return
    const unanswered = questions.filter(q => !selectedAnswers[q.id] || selectedAnswers[q.id].length === 0)
    if (unanswered.length > 0) {
      setUnansweredIds(new Set(unanswered.map(q => q.id)))
      setError(`Please answer all questions. ${unanswered.length} question(s) remaining.`)
      return
    }
    setSubmitting(true)
    setError(null)
    setUnansweredIds(new Set())
    try {
      const res = await submitQuizAttempt(quiz.id, selectedAnswers)
      setResult(res)
    } catch (err: any) {
      setError(err?.response?.data?.detail?.message || 'Failed to submit quiz')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return (
    <div className="flex h-full items-center justify-center">
      <Loader2 className="animate-spin text-accent-blue" size={32} />
    </div>
  )

  if (quizLocked) return (
    <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
      <div className="flex h-20 w-20 items-center justify-center rounded-full bg-navy-800">
        <Lock size={36} className="text-text-secondary" />
      </div>
      <div>
        <h2 className="font-display text-2xl font-bold text-text-primary">Quiz Locked</h2>
        <p className="mt-2 text-text-secondary">Submit the weekly assignment first to unlock the quiz.</p>
      </div>
      <button
        onClick={() => navigate(-1)}
        className="mt-2 flex items-center gap-2 rounded-xl bg-navy-800 px-6 py-2.5 text-sm font-medium text-text-primary hover:bg-navy-700 transition-colors"
      >
        <ChevronLeft size={16} />
        Go Back
      </button>
    </div>
  )

  if (!quiz) return (
    <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
      <div className="flex h-20 w-20 items-center justify-center rounded-full bg-status-warning/10">
        <AlertTriangle size={36} className="text-status-warning" />
      </div>
      <div>
        <h2 className="font-display text-2xl font-bold text-text-primary">No Active Quiz</h2>
        <p className="mt-2 text-text-secondary">{error || 'There is no active quiz for this assignment yet.'}</p>
      </div>
      <button
        onClick={() => navigate(-1)}
        className="mt-2 flex items-center gap-2 rounded-xl bg-navy-800 px-6 py-2.5 text-sm font-medium text-text-primary hover:bg-navy-700 transition-colors"
      >
        <ChevronLeft size={16} />
        Go Back
      </button>
    </div>
  )

  // Show result
  if (result) {
    const pct = result.max_score > 0 ? Math.round((result.total_score / result.max_score) * 100) : 0
    return (
      <div className="mx-auto max-w-3xl space-y-6 p-6">
        <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-sm text-text-secondary hover:text-text-primary transition-colors">
          <ChevronLeft size={16} /> Back to Assignment
        </button>

        <div className="card-glass rounded-2xl p-8 text-center">
          <div className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-accent-blue/10">
            <Trophy size={36} className="text-accent-blue" />
          </div>
          <h1 className="font-display text-3xl font-bold text-text-primary">{quiz?.title}</h1>
          <p className="mt-2 text-text-secondary">Quiz completed!</p>
          <div className="mt-6 flex justify-center gap-8">
            <div className="text-center">
              <p className="text-4xl font-bold text-accent-blue">{result.total_score}</p>
              <p className="mt-1 text-sm text-text-secondary">Score</p>
            </div>
            <div className="text-center">
              <p className="text-4xl font-bold text-text-secondary">{result.max_score}</p>
              <p className="mt-1 text-sm text-text-secondary">Max</p>
            </div>
            <div className="text-center">
              <p className="text-4xl font-bold text-accent-teal">{pct}%</p>
              <p className="mt-1 text-sm text-text-secondary">Percentage</p>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          {result.question_results.map((qr, i) => (
            <div key={qr.question_id} className={`card-glass rounded-xl p-5 border ${qr.is_correct ? 'border-status-success/30' : 'border-status-danger/30'}`}>
              <div className="flex items-start gap-3">
                {qr.is_correct
                  ? <CheckCircle size={20} className="mt-0.5 shrink-0 text-status-success" />
                  : <XCircle size={20} className="mt-0.5 shrink-0 text-status-danger" />
                }
                <div className="flex-1">
                  <p className="font-medium text-text-primary">Q{i + 1}. {qr.question_text}</p>
                  <p className="mt-1 text-sm text-text-secondary">
                    {qr.marks_awarded} / {qr.marks_possible} marks
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  // Show quiz form
  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-sm text-text-secondary hover:text-text-primary transition-colors">
        <ChevronLeft size={16} /> Back to Assignment
      </button>

      <div className="card-glass rounded-2xl p-6">
        <h1 className="font-display text-2xl font-bold text-text-primary">{quiz?.title}</h1>
        <p className="mt-1 text-sm text-text-secondary">{questions.length} question(s) · {quiz?.marks_per_question} mark(s) each</p>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-status-danger/30 bg-status-danger/10 px-4 py-3">
          <AlertTriangle size={16} className="shrink-0 text-status-danger" />
          <p className="text-sm text-status-danger">{error}</p>
        </div>
      )}

      <div className="space-y-4">
        {questions.map((q, i) => {
          const isUnanswered = unansweredIds.has(q.id)
          return (
          <div key={q.id} className={`card-glass rounded-xl p-5 ${isUnanswered ? 'border border-status-danger ring-1 ring-status-danger' : ''}`}>
            <p className="font-medium text-text-primary">
              Q{i + 1}. {q.question_text}
              <span className="ml-2 text-xs text-text-secondary">({q.type === 'multiple' ? 'Select all that apply' : 'Single correct'})</span>
            </p>
            {q.marks && <p className="mt-0.5 text-xs text-text-secondary">{q.marks} marks</p>}
            <div className="mt-3 space-y-2">
              {q.options.map(opt => {
                const selected = (selectedAnswers[q.id] || []).includes(opt.id)
                return (
                  <button
                    key={opt.id}
                    onClick={() => toggleOption(q.id, opt.id, q.type === 'single')}
                    className={`w-full flex items-center gap-3 rounded-lg px-4 py-2.5 text-left text-sm transition-all border
                      ${selected
                        ? 'border-accent-blue bg-accent-blue/10 text-text-primary'
                        : 'border-navy-700 bg-navy-800/40 text-text-secondary hover:border-navy-600 hover:text-text-primary'
                      }`}
                  >
                    <span className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-${q.type === 'single' ? 'full' : 'sm'} border text-xs font-bold
                      ${selected ? 'border-accent-blue bg-accent-blue text-white' : 'border-navy-600'}`}>
                      {selected && '✓'}
                    </span>
                    {opt.option_text}
                  </button>
                )
              })}
            </div>
            {isUnanswered && (
              <p className="mt-3 text-sm text-status-danger font-medium flex items-center gap-1">
                <AlertTriangle size={14} /> Please select an answer.
              </p>
            )}
          </div>
        )})}
      </div>

      <button
        onClick={handleSubmit}
        disabled={submitting}
        className="w-full flex items-center justify-center gap-2 rounded-xl bg-accent-blue py-3 font-medium text-white transition-all hover:bg-[#2471A3] disabled:opacity-60"
      >
        {submitting ? <><Loader2 size={16} className="animate-spin" /> Submitting…</> : 'Submit Quiz'}
      </button>
    </div>
  )
}

export default QuizPage
