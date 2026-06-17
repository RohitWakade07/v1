import { useState, useEffect } from 'react'
import { Megaphone, Check, Loader2, Calendar, Users } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { getStudentAnnouncements, markAnnouncementReadStudent, type AnnouncementPublic } from '@/api/announcements'

const AudienceBadge = ({ audience }: { audience: string }) => {
  const colors: Record<string, string> = {
    students: 'bg-accent-blue/10 text-accent-blue',
    mentors: 'bg-accent-teal/10 text-accent-teal',
    all: 'bg-purple-500/10 text-purple-400',
  }
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${colors[audience] || colors.all}`}>
      <Users size={10} />
      {audience === 'all' ? 'Everyone' : audience.charAt(0).toUpperCase() + audience.slice(1)}
    </span>
  )
}

export const StudentAnnouncementsPage = () => {
  const [announcements, setAnnouncements] = useState<AnnouncementPublic[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const data = await getStudentAnnouncements()
        setAnnouncements(data)
        // Auto-mark all as read
        for (const ann of data.filter((a: AnnouncementPublic) => !a.is_read)) {
          await markAnnouncementReadStudent(ann.id).catch(() => {})
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
      <Loader2 className="animate-spin text-accent-blue" size={28} />
    </div>
  )

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-text-primary">Announcements</h1>
        <p className="text-sm text-text-secondary mt-1">Stay up to date with important updates from admin.</p>
      </div>

      {announcements.length === 0 ? (
        <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-navy-700 p-12 text-center">
          <Megaphone size={36} className="text-text-secondary/40" />
          <p className="text-text-secondary">No announcements yet.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {announcements.map(ann => (
            <div key={ann.id} className={`card-glass rounded-xl p-5 transition-all ${!ann.is_read ? 'border border-accent-blue/30' : ''}`}>
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent-blue/10">
                  <Megaphone size={18} className="text-accent-blue" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-semibold text-text-primary">{ann.title}</h3>
                    {!ann.is_read && <span className="h-2 w-2 rounded-full bg-accent-blue animate-pulse" />}
                    <AudienceBadge audience={ann.audience} />
                  </div>
                  <p className="mt-2 text-sm text-text-secondary whitespace-pre-wrap">{ann.body}</p>
                  <div className="mt-3 flex items-center gap-2 text-xs text-text-secondary/60">
                    <Calendar size={11} />
                    {formatDistanceToNow(new Date(ann.created_at), { addSuffix: true })}
                    {ann.is_read && (
                      <span className="flex items-center gap-1 text-status-success">
                        <Check size={11} /> Read
                      </span>
                    )}
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

export default StudentAnnouncementsPage
