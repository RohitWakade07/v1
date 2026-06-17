import { useState, useEffect } from 'react'
import { Megaphone, Check, Loader2, Calendar } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { getMentorAnnouncements, markAnnouncementReadMentor, type AnnouncementPublic } from '@/api/announcements'

export const MentorAnnouncementsPage = () => {
  const [announcements, setAnnouncements] = useState<AnnouncementPublic[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const data = await getMentorAnnouncements()
        setAnnouncements(data)
        for (const ann of data.filter((a: AnnouncementPublic) => !a.is_read)) {
          await markAnnouncementReadMentor(ann.id).catch(() => {})
        }
        setAnnouncements(data.map((a: AnnouncementPublic) => ({ ...a, is_read: true })))
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return (
    <div className="flex h-full items-center justify-center">
      <Loader2 className="animate-spin text-accent-teal" size={28} />
    </div>
  )

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-text-primary">Announcements</h1>
        <p className="text-sm text-text-secondary mt-1">Platform-wide announcements from the admin team.</p>
      </div>

      {announcements.length === 0 ? (
        <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-navy-700 p-12 text-center">
          <Megaphone size={36} className="text-text-secondary/40" />
          <p className="text-text-secondary">No announcements yet.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {announcements.map(ann => (
            <div key={ann.id} className={`card-glass rounded-xl p-5 ${!ann.is_read ? 'border border-accent-teal/30' : ''}`}>
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent-teal/10">
                  <Megaphone size={18} className="text-accent-teal" />
                </div>
                <div className="flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-semibold text-text-primary">{ann.title}</h3>
                    {!ann.is_read && <span className="h-2 w-2 rounded-full bg-accent-teal animate-pulse" />}
                  </div>
                  <p className="mt-2 text-sm text-text-secondary whitespace-pre-wrap">{ann.body}</p>
                  <div className="mt-3 flex items-center gap-2 text-xs text-text-secondary/60">
                    <Calendar size={11} />
                    {formatDistanceToNow(new Date(ann.created_at), { addSuffix: true })}
                    {ann.is_read && <span className="flex items-center gap-1 text-status-success"><Check size={11} /> Read</span>}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default MentorAnnouncementsPage
