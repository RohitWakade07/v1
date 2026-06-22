import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Lock, CheckCircle, XCircle, AlertTriangle, Loader2, Trophy, ChevronLeft, RefreshCw, BarChart } from 'lucide-react'
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
          if (existing) {
            setResult(existing)
            return
          }
        } catch {
          // Fallback if API still throws an error
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
      // Scroll to top to see error
      window.scrollTo({ top: 0, behavior: 'smooth' })
      return
    }
    setSubmitting(true)
    setError(null)
    setUnansweredIds(new Set())
    try {
      const res = await submitQuizAttempt(quiz.id, selectedAnswers)
      setResult(res)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } catch (err: any) {
      setError(err?.response?.data?.detail?.message || 'Failed to submit quiz')
    } finally {
      setSubmitting(false)
    }
  }

  const handleReattempt = async () => {
    if (!quiz) return
    setLoading(true)
    setResult(null)
    setSelectedAnswers({})
    setUnansweredIds(new Set())
    setError(null)
    try {
      const qs = await getStudentQuizQuestions(quiz.id)
      setQuestions(qs)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } catch (err: any) {
      setError(err?.response?.data?.detail?.message || 'Failed to load questions')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return (
    <div className="flex h-[80vh] items-center justify-center">
      <Loader2 className="animate-spin text-accent-blue" size={32} />
    </div>
  )

  if (quizLocked) return (
    <div className="flex h-[80vh] flex-col items-center justify-center gap-4 text-center px-4">
      <div className="flex h-20 w-20 items-center justify-center rounded-full bg-navy-800 ring-4 ring-navy-800/50">
        <Lock size={36} className="text-text-secondary" />
      </div>
      <div>
        <h2 className="font-display text-2xl font-bold text-text-primary">Quiz Locked</h2>
        <p className="mt-2 text-text-secondary max-w-sm">Submit the weekly assignment first to unlock the quiz. Only successful submissions unlock the test.</p>
      </div>
      <button
        onClick={() => navigate(-1)}
        className="mt-4 flex items-center gap-2 rounded-xl bg-navy-800 px-6 py-2.5 text-sm font-medium text-text-primary hover:bg-navy-700 transition-colors"
      >
        <ChevronLeft size={16} /> Go Back
      </button>
    </div>
  )

  if (!quiz) return (
    <div className="flex h-[80vh] flex-col items-center justify-center gap-4 text-center px-4">
      <div className="flex h-20 w-20 items-center justify-center rounded-full bg-status-warning/10 ring-4 ring-status-warning/5">
        <AlertTriangle size={36} className="text-status-warning" />
      </div>
      <div>
        <h2 className="font-display text-2xl font-bold text-text-primary">No Active Quiz</h2>
        <p className="mt-2 text-text-secondary max-w-sm">{error || 'There is no active quiz for this assignment yet.'}</p>
      </div>
      <button
        onClick={() => navigate(-1)}
        className="mt-4 flex items-center gap-2 rounded-xl bg-navy-800 px-6 py-2.5 text-sm font-medium text-text-primary hover:bg-navy-700 transition-colors"
      >
        <ChevronLeft size={16} /> Go Back
      </button>
    </div>
  )

  // Show result
  if (result) {
    const pct = result.max_score > 0 ? Math.round((result.total_score / result.max_score) * 100) : 0
    const canReattempt = result.attempt_number < result.max_attempts

    return (
      <div className="mx-auto max-w-4xl space-y-6 p-4 md:p-6 pb-20">
        <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-sm text-text-secondary hover:text-text-primary transition-colors">
          <ChevronLeft size={16} /> Back to Assignment
        </button>

        <div className="card-glass rounded-3xl p-6 md:p-10 text-center relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-accent-blue via-accent-teal to-accent-blue"></div>
          
          <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-accent-blue/10 ring-8 ring-accent-blue/5">
            <Trophy size={36} className="text-accent-blue" />
          </div>
          
          <h1 className="font-display text-2xl md:text-4xl font-bold text-text-primary mb-2">{quiz.title}</h1>
          
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-navy-800 text-sm text-text-secondary mb-8">
            <BarChart size={14} />
            Attempt {result.attempt_number} of {result.max_attempts}
          </div>
          
          <div className="flex flex-wrap justify-center gap-4 md:gap-12">
            <div className="text-center bg-navy-900/50 rounded-2xl p-4 min-w-[120px] shadow-inner">
              <p className="text-4xl md:text-5xl font-bold text-accent-blue">{result.total_score}</p>
              <p className="mt-2 text-xs uppercase tracking-wider text-text-secondary font-medium">Your Score</p>
            </div>
            <div className="text-center bg-navy-900/50 rounded-2xl p-4 min-w-[120px] shadow-inner">
              <p className="text-4xl md:text-5xl font-bold text-text-secondary">{result.max_score}</p>
              <p className="mt-2 text-xs uppercase tracking-wider text-text-secondary font-medium">Max Score</p>
            </div>
            <div className="text-center bg-navy-900/50 rounded-2xl p-4 min-w-[120px] shadow-inner relative overflow-hidden">
              <div className="absolute inset-0 opacity-10 bg-accent-teal"></div>
              <p className="text-4xl md:text-5xl font-bold text-accent-teal">{pct}%</p>
              <p className="mt-2 text-xs uppercase tracking-wider text-text-secondary font-medium">Accuracy</p>
            </div>
          </div>
          
          {canReattempt && (
            <div className="mt-10">
              <button 
                onClick={handleReattempt}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-navy-800 border border-navy-600 px-8 py-3.5 font-medium text-text-primary hover:bg-navy-700 hover:border-accent-blue transition-all"
              >
                <RefreshCw size={18} />
                Reattempt Quiz
              </button>
            </div>
          )}
        </div>

        <div className="space-y-4 md:space-y-6">
          <h3 className="font-display text-xl font-bold text-text-primary px-2">Detailed Results</h3>
          {result.question_results.map((qr, i) => (
            <div key={qr.question_id} className={`card-glass rounded-2xl p-5 md:p-6 border-l-4 transition-all duration-300 hover:-translate-y-1 ${qr.is_correct ? 'border-l-status-success border-t-transparent border-r-transparent border-b-transparent' : 'border-l-status-danger border-t-transparent border-r-transparent border-b-transparent'}`}>
              <div className="flex flex-col md:flex-row md:items-start gap-4">
                <div className="flex items-center gap-3 md:w-full">
                  {qr.is_correct
                    ? <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-status-success/10"><CheckCircle size={22} className="text-status-success" /></div>
                    : <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-status-danger/10"><XCircle size={22} className="text-status-danger" /></div>
                  }
                  <div className="flex-1">
                    <p className="font-medium text-text-primary text-base md:text-lg leading-relaxed"><span className="text-text-secondary font-mono text-sm mr-2">Q{i + 1}.</span>{qr.question_text}</p>
                    <div className="mt-2 inline-flex items-center gap-1.5 rounded-full bg-navy-900/80 px-2.5 py-1 text-xs font-medium text-text-secondary">
                      {qr.marks_awarded} / {qr.marks_possible} marks
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  // Show quiz form
  const answeredCount = Object.keys(selectedAnswers).filter(k => selectedAnswers[k].length > 0).length
  const progressPct = questions.length > 0 ? (answeredCount / questions.length) * 100 : 0

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-4 md:p-6 pb-32">
      <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-sm text-text-secondary hover:text-text-primary transition-colors">
        <ChevronLeft size={16} /> Back to Assignment
      </button>

      <div className="card-glass rounded-3xl p-6 md:p-8 relative overflow-hidden">
        <div className="absolute top-0 left-0 h-1 bg-navy-800 w-full">
          <div className="h-full bg-accent-blue transition-all duration-500 ease-out" style={{ width: `${progressPct}%` }}></div>
        </div>
        
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="font-display text-2xl md:text-3xl font-bold text-text-primary">{quiz.title}</h1>
            <p className="mt-2 text-sm text-text-secondary flex items-center gap-2">
              <span className="bg-navy-800 px-2 py-0.5 rounded text-xs font-medium">{questions.length} Questions</span>
              <span>·</span>
              <span>{quiz.marks_per_question} marks each</span>
            </p>
          </div>
          
          <div className="text-left md:text-right">
            <p className="text-sm font-medium text-text-primary">{answeredCount} of {questions.length} answered</p>
          </div>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-3 rounded-2xl border border-status-danger/30 bg-status-danger/10 px-5 py-4 animate-in fade-in slide-in-from-top-2">
          <AlertTriangle size={20} className="shrink-0 text-status-danger" />
          <p className="text-sm font-medium text-status-danger">{error}</p>
        </div>
      )}

      <div className="space-y-6">
        {questions.map((q, i) => {
          const isUnanswered = unansweredIds.has(q.id)
          const isAnswered = (selectedAnswers[q.id] || []).length > 0
          
          return (
          <div key={q.id} className={`card-glass rounded-3xl p-5 md:p-8 transition-all duration-300 ${isUnanswered ? 'border border-status-danger ring-2 ring-status-danger/20 shadow-[0_0_15px_rgba(239,68,68,0.1)]' : ''} ${isAnswered && !isUnanswered ? 'border-accent-blue/30 bg-accent-blue/[0.02]' : ''}`}>
            <div className="flex flex-col md:flex-row md:items-start gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-navy-800 text-sm font-bold text-text-secondary border border-navy-700">
                {i + 1}
              </div>
              <div className="flex-1 w-full">
                <p className="font-medium text-text-primary text-base md:text-lg leading-relaxed">
                  {q.question_text}
                </p>
                
                <div className="mt-3 flex items-center gap-2">
                  <span className="inline-flex items-center rounded-full bg-navy-800 px-2.5 py-1 text-xs font-medium text-text-secondary">
                    {q.type === 'multiple' ? 'Select all that apply' : 'Select one'}
                  </span>
                  {q.marks && (
                    <span className="inline-flex items-center rounded-full bg-navy-800 px-2.5 py-1 text-xs font-medium text-text-secondary">
                      {q.marks} marks
                    </span>
                  )}
                </div>

                <div className="mt-6 space-y-3">
                  {q.options.map(opt => {
                    const selected = (selectedAnswers[q.id] || []).includes(opt.id)
                    return (
                      <button
                        key={opt.id}
                        onClick={() => toggleOption(q.id, opt.id, q.type === 'single')}
                        className={`w-full group flex items-start gap-4 rounded-2xl px-5 py-4 text-left text-sm md:text-base transition-all duration-200 border
                          ${selected
                            ? 'border-accent-blue bg-accent-blue/10 text-text-primary shadow-[inset_0_0_0_1px_rgba(59,130,246,0.5)]'
                            : 'border-navy-700 bg-navy-800/40 text-text-secondary hover:border-navy-600 hover:bg-navy-800 hover:text-text-primary shadow-sm'
                          }`}
                      >
                        <div className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-${q.type === 'single' ? 'full' : 'md'} border-2 transition-colors
                          ${selected ? 'border-accent-blue bg-accent-blue text-white' : 'border-navy-600 group-hover:border-navy-500'}`}>
                          {selected && <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>}
                        </div>
                        <span className="leading-relaxed">{opt.option_text}</span>
                      </button>
                    )
                  })}
                </div>
                {isUnanswered && (
                  <p className="mt-4 text-sm text-status-danger font-medium flex items-center gap-1.5 bg-status-danger/10 px-3 py-2 rounded-lg w-fit animate-in fade-in">
                    <AlertTriangle size={16} /> Please select an answer to continue.
                  </p>
                )}
              </div>
            </div>
          </div>
        )})}
      </div>

      <div className="fixed bottom-0 left-0 right-0 p-4 bg-navy-900/80 backdrop-blur-xl border-t border-navy-800 z-10 lg:static lg:bg-transparent lg:backdrop-blur-none lg:border-none lg:p-0">
        <div className="max-w-4xl mx-auto flex items-center justify-between gap-4">
          <div className="hidden lg:block text-sm text-text-secondary font-medium">
            Make sure to review all answers before submitting
          </div>
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="w-full lg:w-auto flex-1 lg:flex-none items-center justify-center gap-2 rounded-xl bg-accent-blue px-10 py-4 font-bold text-white transition-all hover:bg-accent-blue/90 hover:shadow-[0_0_20px_rgba(59,130,246,0.3)] disabled:opacity-60 disabled:hover:shadow-none"
          >
            {submitting ? <><Loader2 size={18} className="animate-spin inline mr-2" /> Submitting…</> : 'Submit Quiz'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default QuizPage
