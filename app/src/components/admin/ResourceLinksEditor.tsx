import { useState, useCallback } from 'react'
import { Link2, Video, Image as ImageIcon, Trash2, Plus, GripVertical, ExternalLink } from 'lucide-react'

export type ResourceType = 'link' | 'video' | 'image'

export interface ResourceLink {
  title: string
  url: string
  type: ResourceType
}

interface Props {
  value: ResourceLink[]
  onChange: (links: ResourceLink[]) => void
}

const TYPE_CONFIG: Record<ResourceType, { label: string; icon: React.ReactNode; color: string; placeholder: string }> = {
  link: {
    label: 'Link',
    icon: <Link2 size={12} />,
    color: 'text-accent-blue border-accent-blue/30 bg-accent-blue/10',
    placeholder: 'https://docs.example.com/guide',
  },
  video: {
    label: 'Video',
    icon: <Video size={12} />,
    color: 'text-red-400 border-red-400/30 bg-red-400/10',
    placeholder: 'https://youtube.com/watch?v=...',
  },
  image: {
    label: 'Image',
    icon: <ImageIcon size={12} />,
    color: 'text-purple-400 border-purple-400/30 bg-purple-400/10',
    placeholder: 'https://example.com/diagram.png',
  },
}

export function ResourceLinksEditor({ value, onChange }: Props) {
  const [newTitle, setNewTitle] = useState('')
  const [newUrl, setNewUrl] = useState('')
  const [newType, setNewType] = useState<ResourceType>('link')

  const addResource = useCallback(() => {
    if (!newTitle.trim() || !newUrl.trim()) return
    const url = newUrl.trim().startsWith('http') ? newUrl.trim() : `https://${newUrl.trim()}`
    onChange([...value, { title: newTitle.trim(), url, type: newType }])
    setNewTitle('')
    setNewUrl('')
  }, [newTitle, newUrl, newType, value, onChange])

  const removeResource = (index: number) => {
    onChange(value.filter((_, i) => i !== index))
  }

  const autoDetectType = (url: string): ResourceType => {
    const lower = url.toLowerCase()
    if (lower.includes('youtube.com') || lower.includes('youtu.be') || lower.includes('vimeo')) return 'video'
    if (lower.match(/\.(png|jpg|jpeg|gif|webp|svg)(\?|$)/)) return 'image'
    return 'link'
  }

  const handleUrlChange = (url: string) => {
    setNewUrl(url)
    if (url.length > 8) setNewType(autoDetectType(url))
  }

  return (
    <div className="space-y-3">
      {/* Existing resources */}
      {value.length > 0 ? (
        <div className="space-y-2 max-h-[240px] overflow-y-auto pr-1">
          {value.map((link, i) => {
            const cfg = TYPE_CONFIG[link.type || 'link']
            return (
              <div
                key={i}
                className="flex items-center gap-2 rounded-lg border border-navy-800 bg-navy-900/50 p-2.5 group hover:border-navy-700 transition-colors"
              >
                <GripVertical size={14} className="text-text-muted shrink-0" />
                <span className={`flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded border ${cfg.color} shrink-0`}>
                  {cfg.icon} {cfg.label}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-text-primary truncate">{link.title}</p>
                  <a
                    href={link.url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1 text-[10px] text-text-muted hover:text-accent-blue truncate transition-colors"
                  >
                    {link.url.replace(/^https?:\/\//, '').slice(0, 50)}
                    <ExternalLink size={9} className="shrink-0" />
                  </a>
                </div>
                <button
                  onClick={() => removeResource(i)}
                  className="opacity-0 group-hover:opacity-100 text-status-danger hover:text-status-danger/80 transition-all shrink-0"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="text-center py-6 border border-dashed border-navy-800 rounded-lg text-text-muted text-xs">
          No resources added yet. Add links, videos or images below.
        </div>
      )}

      {/* Add new resource form */}
      <div className="rounded-lg border border-navy-700 bg-navy-900/30 p-3 space-y-2">
        <p className="text-[10px] font-semibold text-text-secondary uppercase tracking-wider">Add Resource</p>

        {/* Type selector */}
        <div className="flex gap-1">
          {(Object.keys(TYPE_CONFIG) as ResourceType[]).map((t) => {
            const cfg = TYPE_CONFIG[t]
            return (
              <button
                key={t}
                type="button"
                onClick={() => setNewType(t)}
                className={`flex items-center gap-1 text-[10px] font-semibold px-2 py-1 rounded border transition-all ${
                  newType === t ? cfg.color : 'text-text-muted border-navy-700 hover:border-navy-600'
                }`}
              >
                {cfg.icon} {cfg.label}
              </button>
            )
          })}
        </div>

        <input
          type="text"
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          placeholder="Resource title (e.g. Week 1 Tutorial)"
          className="input-dark w-full text-xs"
        />
        <div className="flex gap-2">
          <input
            type="text"
            value={newUrl}
            onChange={(e) => handleUrlChange(e.target.value)}
            placeholder={TYPE_CONFIG[newType].placeholder}
            className="input-dark flex-1 text-xs font-mono"
            onKeyDown={(e) => e.key === 'Enter' && addResource()}
          />
          <button
            type="button"
            onClick={addResource}
            disabled={!newTitle.trim() || !newUrl.trim()}
            className="flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg bg-accent-blue text-white hover:bg-accent-blue/80 disabled:opacity-40 disabled:cursor-not-allowed transition-colors shrink-0"
          >
            <Plus size={12} /> Add
          </button>
        </div>
      </div>
    </div>
  )
}
