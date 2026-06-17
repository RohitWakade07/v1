import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import {
  Megaphone, Plus, Pencil, Trash2, Loader2, Calendar, Check, X, Users, AlertTriangle
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import {
  getAdminAnnouncements, createAnnouncement, updateAnnouncement, deleteAnnouncement,
  type AnnouncementPublic,
} from '@/api/announcements'

const AUDIENCE_OPTIONS = [
  { value: 'all', label: 'Everyone', color: 'text-purple-400' },
  { value: 'students', label: 'Students Only', color: 'text-accent-blue' },
  { value: 'mentors', label: 'Mentors Only', color: 'text-accent-teal' },
]

interface AnnFormState {
  title: string
  body: string
  audience: string
  expires_at: string
}

const EMPTY_FORM: AnnFormState = { title: '', body: '', audience: 'all', expires_at: '' }

export const AdminAnnouncementsPage = () => {
  const [announcements, setAnnouncements] = useState<AnnouncementPublic[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState<AnnFormState>(EMPTY_FORM)
  const [saving, setSaving] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    setLoading(true)
    try {
      const data = await getAdminAnnouncements()
      setAnnouncements(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const openCreate = () => {
    setEditingId(null)
    setForm(EMPTY_FORM)
    setError(null)
    setShowForm(true)
  }

  const openEdit = (ann: AnnouncementPublic) => {
    setEditingId(ann.id)
    setForm({
      title: ann.title,
      body: ann.body,
      audience: ann.audience,
      expires_at: ann.expires_at ? ann.expires_at.slice(0, 16) : '',
    })
    setError(null)
    setShowForm(true)
  }

  const handleSave = async () => {
    if (!form.title.trim() || !form.body.trim()) {
      setError('Title and body are required.')
      return
    }
    setSaving(true)
    setError(null)
    try {
      const payload = {
        title: form.title.trim(),
        body: form.body.trim(),
        audience: form.audience,
        ...(form.expires_at ? { expires_at: new Date(form.expires_at).toISOString() } : {}),
      }
      if (editingId) {
        await updateAnnouncement(editingId, payload)
      } else {
        await createAnnouncement(payload)
      }
      setShowForm(false)
      await load()
    } catch (err: any) {
      setError(err?.response?.data?.detail?.message || 'Failed to save announcement.')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: string) => {
    setDeletingId(id)
    try {
      await deleteAnnouncement(id)
      setAnnouncements(prev => prev.filter(a => a.id !== id))
    } catch (err: any) {
      alert(err?.response?.data?.detail?.message || 'Failed to delete.')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-text-primary">Announcements</h1>
          <p className="text-sm text-text-secondary mt-1">Create and manage platform-wide announcements.</p>
        </div>
        <button
          onClick={openCreate}
          className="flex items-center gap-2 rounded-xl bg-accent-blue px-5 py-2.5 text-sm font-medium text-white transition-all hover:bg-[#2471A3]"
        >
          <Plus size={16} /> New Announcement
        </button>
      </div>

      {/* Form Modal */}
      {showForm && createPortal(
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-xl card-glass rounded-2xl p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between">
              <h2 className="font-display text-lg font-bold text-text-primary">
                {editingId ? 'Edit Announcement' : 'New Announcement'}
              </h2>
              <button onClick={() => setShowForm(false)} className="text-text-secondary hover:text-text-primary">
                <X size={20} />
              </button>
            </div>

            {error && (
              <div className="flex items-center gap-2 rounded-lg border border-status-danger/30 bg-status-danger/10 px-3 py-2 text-sm text-status-danger">
                <AlertTriangle size={14} className="shrink-0" />
                {error}
              </div>
            )}

            <div>
              <label className="mb-1 block text-xs font-medium text-text-secondary">Title *</label>
              <input
                className="input-dark w-full"
                placeholder="Announcement title"
                value={form.title}
                onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
              />
            </div>

            <div>
              <label className="mb-1 block text-xs font-medium text-text-secondary">Body *</label>
              <textarea
                className="input-dark w-full resize-none"
                rows={4}
                placeholder="Announcement body..."
                value={form.body}
                onChange={e => setForm(f => ({ ...f, body: e.target.value }))}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="mb-1 block text-xs font-medium text-text-secondary">Target Audience</label>
                <select
                  className="input-dark w-full"
                  value={form.audience}
                  onChange={e => setForm(f => ({ ...f, audience: e.target.value }))}
                >
                  {AUDIENCE_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-text-secondary">Expires At (optional)</label>
                <input
                  type="datetime-local"
                  className="input-dark w-full"
                  value={form.expires_at}
                  onChange={e => setForm(f => ({ ...f, expires_at: e.target.value }))}
                />
              </div>
            </div>

            <div className="flex gap-3 pt-2">
              <button
                onClick={() => setShowForm(false)}
                className="flex-1 rounded-xl border border-navy-700 py-2.5 text-sm font-medium text-text-secondary hover:text-text-primary transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex-1 flex items-center justify-center gap-2 rounded-xl bg-accent-blue py-2.5 text-sm font-medium text-white transition-all hover:bg-[#2471A3] disabled:opacity-60"
              >
                {saving ? <><Loader2 size={14} className="animate-spin" /> Saving…</> : <><Check size={14} /> {editingId ? 'Update' : 'Publish'}</>}
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}

      {/* List */}
      {loading ? (
        <div className="flex h-40 items-center justify-center">
          <Loader2 className="animate-spin text-accent-blue" size={28} />
        </div>
      ) : announcements.length === 0 ? (
        <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-navy-700 p-12 text-center">
          <Megaphone size={36} className="text-text-secondary/40" />
          <p className="text-text-secondary">No announcements yet. Create your first one!</p>
        </div>
      ) : (
        <div className="space-y-4">
          {announcements.map(ann => (
            <div key={ann.id} className="card-glass rounded-xl p-5">
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent-blue/10">
                  <Megaphone size={18} className="text-accent-blue" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-semibold text-text-primary">{ann.title}</h3>
                    <span className={`flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium
                      ${ann.audience === 'students' ? 'bg-accent-blue/10 text-accent-blue'
                        : ann.audience === 'mentors' ? 'bg-accent-teal/10 text-accent-teal'
                        : 'bg-purple-500/10 text-purple-400'}`}>
                      <Users size={10} />
                      {ann.audience === 'all' ? 'Everyone' : ann.audience.charAt(0).toUpperCase() + ann.audience.slice(1)}
                    </span>
                  </div>
                  <p className="mt-1.5 text-sm text-text-secondary whitespace-pre-wrap line-clamp-3">{ann.body}</p>
                  <div className="mt-2 flex items-center gap-3 text-xs text-text-secondary/60">
                    <span className="flex items-center gap-1"><Calendar size={11} /> {formatDistanceToNow(new Date(ann.created_at), { addSuffix: true })}</span>
                    {ann.expires_at && <span>Expires {formatDistanceToNow(new Date(ann.expires_at), { addSuffix: true })}</span>}
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button onClick={() => openEdit(ann)} className="rounded-lg p-2 text-text-secondary hover:text-text-primary hover:bg-navy-700/50 transition-colors">
                    <Pencil size={14} />
                  </button>
                  <button
                    onClick={() => handleDelete(ann.id)}
                    disabled={deletingId === ann.id}
                    className="rounded-lg p-2 text-text-secondary hover:text-status-danger hover:bg-status-danger/10 transition-colors"
                  >
                    {deletingId === ann.id ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default AdminAnnouncementsPage
