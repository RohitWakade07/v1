import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Plus, Pencil, Trash2, Loader2, ChevronLeft, Save, UploadCloud, Download
} from 'lucide-react'
import {
  getAdminQuiz, createAdminQuiz, updateAdminQuiz, getAdminQuizQuestions,
  addQuestion, editQuestion, deleteQuestion, importQuestionsCSV, downloadQuizCSVTemplate,
  type QuizPublic, type QuizQuestion
} from '@/api/student/quiz'

export const AdminQuizPage = () => {
  const { assignmentId } = useParams<{ assignmentId: string }>()
  const navigate = useNavigate()

  const [quiz, setQuiz] = useState<QuizPublic | null>(null)
  const [questions, setQuestions] = useState<QuizQuestion[]>([])
  const [loading, setLoading] = useState(true)

  // Edit / Create Quiz state
  const [quizForm, setQuizForm] = useState({ title: '', marks_per_question: 1, is_active: false })
  const [savingQuiz, setSavingQuiz] = useState(false)

  // Question Modal state
  const [showQModal, setShowQModal] = useState(false)
  const [editingQId, setEditingQId] = useState<string | null>(null)
  const [qForm, setQForm] = useState({
    question_text: '',
    type: 'single' as 'single' | 'multiple',
    marks: 1,
    options: [
      { text: '', is_correct: false },
      { text: '', is_correct: false },
      { text: '', is_correct: false },
      { text: '', is_correct: false }
    ]
  })
  const [savingQ, setSavingQ] = useState(false)

  // CSV Import
  const [importing, setImporting] = useState(false)

  const load = async () => {
    if (!assignmentId) return
    setLoading(true)
    try {
      const q = await getAdminQuiz(assignmentId)
      setQuiz(q)
      setQuizForm({ title: q.title, marks_per_question: q.marks_per_question, is_active: q.is_active })
      const qs = await getAdminQuizQuestions(q.id)
      setQuestions(qs)
    } catch (err: any) {
      if (err?.response?.status === 404) {
        setQuiz(null)
      } else {
        alert('Failed to load quiz')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [assignmentId])

  const handleSaveQuiz = async () => {
    if (!assignmentId || !quizForm.title) return
    setSavingQuiz(true)
    try {
      if (quiz) {
        const q = await updateAdminQuiz(quiz.id, quizForm)
        setQuiz(q)
      } else {
        const q = await createAdminQuiz(assignmentId, quizForm)
        setQuiz(q)
      }
    } catch (err: any) {
      alert('Failed to save quiz settings')
    } finally {
      setSavingQuiz(false)
    }
  }

  const handleSaveQuestion = async () => {
    if (!quiz) return
    if (!qForm.question_text || qForm.options.some(o => !o.text)) {
      alert('Question and all options must have text.')
      return
    }
    if (!qForm.options.some(o => o.is_correct)) {
      alert('At least one option must be marked as correct.')
      return
    }
    setSavingQ(true)
    try {
      const payload = {
        question_text: qForm.question_text,
        type: qForm.type,
        marks: qForm.marks,
        order_index: questions.length,
        options: qForm.options.map((o, i) => ({ option_text: o.text, is_correct: o.is_correct, order_index: i }))
      }
      if (editingQId) {
        await editQuestion(editingQId, payload)
      } else {
        await addQuestion(quiz.id, payload)
      }
      setShowQModal(false)
      const qs = await getAdminQuizQuestions(quiz.id)
      setQuestions(qs)
    } catch (err) {
      alert('Failed to save question')
    } finally {
      setSavingQ(false)
    }
  }

  const handleDeleteQ = async (id: string) => {
    if (!confirm('Delete this question?')) return
    try {
      await deleteQuestion(id)
      setQuestions(prev => prev.filter(q => q.id !== id))
    } catch {
      alert('Failed to delete')
    }
  }

  const openNewQ = () => {
    setEditingQId(null)
    setQForm({
      question_text: '',
      type: 'single',
      marks: quiz?.marks_per_question || 1,
      options: [
        { text: '', is_correct: false },
        { text: '', is_correct: false },
        { text: '', is_correct: false },
        { text: '', is_correct: false }
      ]
    })
    setShowQModal(true)
  }

  const openEditQ = (q: QuizQuestion) => {
    setEditingQId(q.id)
    setQForm({
      question_text: q.question_text,
      type: q.type,
      marks: q.marks || quiz?.marks_per_question || 1,
      options: q.options.map(o => ({ text: o.option_text, is_correct: o.is_correct || false }))
    })
    setShowQModal(true)
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || !quiz) return
    setImporting(true)
    try {
      await importQuestionsCSV(quiz.id, file)
      const qs = await getAdminQuizQuestions(quiz.id)
      setQuestions(qs)
      alert('Imported successfully')
    } catch (err: any) {
      alert(err?.response?.data?.detail?.message || 'Failed to import CSV')
    } finally {
      setImporting(false)
      if (e.target) e.target.value = ''
    }
  }

  if (loading) return (
    <div className="flex h-full items-center justify-center">
      <Loader2 className="animate-spin text-accent-blue" size={32} />
    </div>
  )

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-sm text-text-secondary hover:text-text-primary transition-colors">
        <ChevronLeft size={16} /> Back
      </button>

      <div className="card-glass rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-display text-2xl font-bold text-text-primary">
              {quiz ? 'Quiz Settings' : 'Create Quiz'}
            </h1>
            <p className="text-sm text-text-secondary mt-1">Configure quiz requirements for this weekly task.</p>
          </div>
          {quiz && (
            <div className="flex items-center gap-3">
              <label className="flex items-center gap-2 text-sm text-text-secondary">
                <input
                  type="checkbox"
                  checked={quizForm.is_active}
                  onChange={e => setQuizForm(f => ({ ...f, is_active: e.target.checked }))}
                  className="rounded border-navy-600 bg-navy-800 text-accent-blue focus:ring-accent-blue"
                />
                Active
              </label>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-text-secondary">Quiz Title</label>
            <input
              className="input-dark w-full"
              placeholder="e.g. Week 1 Self Assessment"
              value={quizForm.title}
              onChange={e => setQuizForm(f => ({ ...f, title: e.target.value }))}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-text-secondary">Default Marks per Question</label>
            <input
              type="number"
              className="input-dark w-full"
              value={quizForm.marks_per_question}
              onChange={e => setQuizForm(f => ({ ...f, marks_per_question: Number(e.target.value) }))}
            />
          </div>
        </div>
        <button
          onClick={handleSaveQuiz}
          disabled={savingQuiz || !quizForm.title}
          className="flex items-center gap-2 rounded-xl bg-navy-800 px-5 py-2 text-sm font-medium text-text-primary hover:bg-navy-700 transition-colors disabled:opacity-50"
        >
          {savingQuiz ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
          {quiz ? 'Save Settings' : 'Create Quiz to Add Questions'}
        </button>
      </div>

      {quiz && (
        <div className="card-glass rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-navy-700/50 pb-4">
            <div>
              <h2 className="font-display text-lg font-bold text-text-primary">Questions ({questions.length})</h2>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={downloadQuizCSVTemplate}
                className="flex items-center gap-2 text-xs text-accent-blue hover:text-accent-teal transition-colors"
              >
                <Download size={14} /> CSV Template
              </button>
              <label className="flex items-center gap-2 rounded-xl border border-navy-600 px-4 py-2 text-sm font-medium text-text-secondary hover:text-text-primary hover:bg-navy-800 cursor-pointer transition-colors">
                {importing ? <Loader2 size={16} className="animate-spin" /> : <UploadCloud size={16} />}
                Import CSV
                <input type="file" accept=".csv" className="hidden" onChange={handleFileUpload} disabled={importing} />
              </label>
              <button
                onClick={openNewQ}
                className="flex items-center gap-2 rounded-xl bg-accent-blue px-4 py-2 text-sm font-medium text-white transition-all hover:bg-[#2471A3]"
              >
                <Plus size={16} /> Add Question
              </button>
            </div>
          </div>

          <div className="space-y-3">
            {questions.map((q, i) => (
              <div key={q.id} className="rounded-xl border border-navy-700 bg-navy-800/20 p-4 flex items-start justify-between">
                <div>
                  <p className="font-medium text-text-primary text-sm flex gap-2">
                    <span className="text-text-secondary">Q{i + 1}.</span> {q.question_text}
                  </p>
                  <p className="mt-1 text-xs text-text-secondary">
                    Type: {q.type} | Marks: {q.marks || quiz.marks_per_question}
                  </p>
                </div>
                <div className="flex gap-2 shrink-0">
                  <button onClick={() => openEditQ(q)} className="p-1.5 text-text-secondary hover:text-text-primary bg-navy-800 rounded-lg"><Pencil size={14}/></button>
                  <button onClick={() => handleDeleteQ(q.id)} className="p-1.5 text-text-secondary hover:text-status-danger bg-navy-800 rounded-lg"><Trash2 size={14}/></button>
                </div>
              </div>
            ))}
            {questions.length === 0 && (
              <div className="text-center p-8 text-text-secondary text-sm border border-dashed border-navy-700 rounded-xl">
                No questions yet. Add one manually or import from CSV.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Question Modal */}
      {showQModal && createPortal(
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 p-4">
          <div className="w-full max-w-xl card-glass rounded-2xl p-6 space-y-4">
            <h2 className="font-display text-lg font-bold text-text-primary">
              {editingQId ? 'Edit Question' : 'Add Question'}
            </h2>
            <div>
              <label className="mb-1 block text-xs font-medium text-text-secondary">Question Text</label>
              <textarea
                className="input-dark w-full resize-none" rows={3}
                value={qForm.question_text}
                onChange={e => setQForm(f => ({ ...f, question_text: e.target.value }))}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="mb-1 block text-xs font-medium text-text-secondary">Type</label>
                <select
                  className="input-dark w-full"
                  value={qForm.type}
                  onChange={e => setQForm(f => ({ ...f, type: e.target.value as 'single'|'multiple' }))}
                >
                  <option value="single">Single Correct</option>
                  <option value="multiple">Multiple Correct</option>
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-text-secondary">Marks</label>
                <input
                  type="number" className="input-dark w-full"
                  value={qForm.marks}
                  onChange={e => setQForm(f => ({ ...f, marks: Number(e.target.value) }))}
                />
              </div>
            </div>
            <div>
              <label className="mb-2 block text-xs font-medium text-text-secondary">Options (Check the correct ones)</label>
              <div className="space-y-2">
                {qForm.options.map((opt, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <input
                      type={qForm.type === 'single' ? 'radio' : 'checkbox'}
                      name={qForm.type === 'single' ? 'correct_opt' : undefined}
                      checked={opt.is_correct}
                      onChange={e => {
                        const newOpts = [...qForm.options]
                        if (qForm.type === 'single') {
                          newOpts.forEach(o => o.is_correct = false)
                        }
                        newOpts[i].is_correct = e.target.checked
                        setQForm(f => ({ ...f, options: newOpts }))
                      }}
                      className="w-4 h-4 text-accent-blue bg-navy-800 border-navy-600 focus:ring-accent-blue"
                    />
                    <input
                      className="input-dark flex-1 py-1.5 text-sm"
                      placeholder={`Option ${String.fromCharCode(65 + i)}`}
                      value={opt.text}
                      onChange={e => {
                        const newOpts = [...qForm.options]
                        newOpts[i].text = e.target.value
                        setQForm(f => ({ ...f, options: newOpts }))
                      }}
                    />
                  </div>
                ))}
              </div>
            </div>
            <div className="flex gap-3 pt-4">
              <button onClick={() => setShowQModal(false)} className="flex-1 border border-navy-700 py-2 rounded-xl text-sm font-medium hover:text-white">Cancel</button>
              <button onClick={handleSaveQuestion} disabled={savingQ} className="flex-1 bg-accent-blue py-2 rounded-xl text-sm font-medium text-white hover:bg-[#2471A3]">
                {savingQ ? 'Saving...' : 'Save Question'}
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  )
}

export default AdminQuizPage
