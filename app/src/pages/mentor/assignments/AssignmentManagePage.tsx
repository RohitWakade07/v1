import { useState } from 'react'
import { Calendar, ToggleLeft, ToggleRight, Clock, CheckCircle2, Lock, ChevronDown, ChevronUp, BookOpen, Terminal, GitBranch, GitPullRequest, Code2, Globe, Layers, Search } from 'lucide-react'
import { PageWrapper } from '@/components/shared/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { useAssignments } from '@/hooks/mentor/useAssignments'
import { usePublishAssignment, useUnpublishAssignment } from '@/hooks/mentor/usePublishAssignment'
import { useUpdateAssignment } from '@/hooks/mentor/useUpdateAssignment'
import type { Assignment } from '@/types/api'
import { cn } from '@/lib/utils'

// ── Static metadata for all 9 weeks ──────────────────────────────────────────
const WEEK_META = [
  {
    slug: 'week1',
    week: 1,
    title: 'Week 1: Workspace Setup',
    subtitle: 'Linux Environment & Filesystem Navigation',
    description: 'Students build a clean developer workspace using shell commands — creating directory trees, READMEs, aliases, and a workspace report.',
    icon: Terminal,
    color: 'accent-blue',
    file: 'commands.txt',
    marks: 5,
  },
  {
    slug: 'week2',
    week: 2,
    title: 'Week 2: Log Analyzer',
    subtitle: 'Command-Line Tools & Text Processing',
    description: 'Students write a shell pipeline script to analyse server logs and produce a report with top IPs, URLs, status codes, and request count.',
    icon: Search,
    color: 'accent-teal',
    file: 'analyze.sh',
    marks: 5,
  },
  {
    slug: 'week3',
    week: 3,
    title: 'Week 3: File Organizer',
    subtitle: 'Shell Scripting & Automation',
    description: 'Students write a Bash script that auto-sorts a messy directory into Documents, Images, Code, and Other sub-folders.',
    icon: Layers,
    color: 'accent-blue',
    file: 'organize.sh',
    marks: 5,
  },
  {
    slug: 'week4',
    week: 4,
    title: 'Week 4: Git Recovery',
    subtitle: 'Version Control with Git',
    description: 'Students receive a broken repository and must fix the .gitignore, amend commits, merge branches, and document every step.',
    icon: GitBranch,
    color: 'accent-teal',
    file: 'RECOVERY.md + repo',
    marks: 5,
  },
  {
    slug: 'week5',
    week: 5,
    title: 'Week 5: GitHub Collaboration',
    subtitle: 'Collaborative Development with GitHub',
    description: 'Pairs of students resolve merge conflicts, review PRs, and push a clean main branch with a shared TEAMWORK.md.',
    icon: GitPullRequest,
    color: 'accent-blue',
    file: 'TEAMWORK.md + repo',
    marks: 5,
  },
  {
    slug: 'week6',
    week: 6,
    title: 'Week 6: Text Corpus Analyzer',
    subtitle: 'Python Foundations & Computational Thinking',
    description: 'Students build an interactive Python CLI that provides word stats, top-N frequency, and cross-file word search on a text corpus.',
    icon: Code2,
    color: 'accent-teal',
    file: 'analyze.py',
    marks: 5,
  },
  {
    slug: 'week7',
    week: 7,
    title: 'Week 7: Wikipedia Collector',
    subtitle: 'Web Scraping & Dataset Collection',
    description: 'Students build a scraper that fetches Wikipedia pages from a URL list and saves each as a structured JSON file.',
    icon: Globe,
    color: 'accent-blue',
    file: 'collect_wiki.py',
    marks: 5,
  },
  {
    slug: 'week8',
    week: 8,
    title: 'Week 8: Metadata Organizer',
    subtitle: 'Functions, Modularity & Data Structures',
    description: 'Students build a modular Python package that processes the Week 7 corpus and outputs per-document and corpus-level metadata.',
    icon: BookOpen,
    color: 'accent-teal',
    file: 'metadata_organizer/ package',
    marks: 5,
  },
  {
    slug: 'week9',
    week: 9,
    title: 'Week 9: Inverted Index',
    subtitle: 'Linear vs Inverted Index & Frequency Counting',
    description: 'Students build an inverted index from their corpus and a lookup tool that returns documents sorted by term frequency.',
    icon: Search,
    color: 'accent-blue',
    file: 'build_index.py + lookup.py',
    marks: 5,
  },
]

// ── Deadline Editor ───────────────────────────────────────────────────────────
function DeadlineEditor({
  assignment,
  onSave,
  isSaving,
}: {
  assignment: Assignment
  onSave: (deadline: string) => void
  isSaving: boolean
}) {
  const [editing, setEditing] = useState(false)
  const current = assignment.deadline
    ? new Date(assignment.deadline).toISOString().slice(0, 16)
    : ''
  const [value, setValue] = useState(current)

  const handleSave = () => {
    onSave(value)
    setEditing(false)
  }

  if (!editing) {
    return (
      <button
        onClick={() => setEditing(true)}
        className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs text-text-secondary hover:bg-navy-800 hover:text-text-primary transition-colors group"
        title="Click to edit deadline"
      >
        <Calendar size={12} className="text-accent-blue group-hover:scale-110 transition-transform" />
        {assignment.deadline
          ? new Date(assignment.deadline).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
          : <span className="italic text-text-muted">No deadline</span>}
      </button>
    )
  }

  return (
    <div className="flex items-center gap-2">
      <input
        type="datetime-local"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        className="input-dark text-xs py-1 px-2 w-48"
        autoFocus
      />
      <button
        onClick={handleSave}
        disabled={isSaving}
        className="rounded-lg bg-accent-blue px-2.5 py-1 text-xs font-semibold text-white hover:bg-accent-blue/80 disabled:opacity-50 transition-colors"
      >
        {isSaving ? '…' : 'Save'}
      </button>
      <button
        onClick={() => setEditing(false)}
        className="rounded-lg px-2 py-1 text-xs text-text-secondary hover:bg-navy-800 transition-colors"
      >
        Cancel
      </button>
    </div>
  )
}

// ── Assignment Card ───────────────────────────────────────────────────────────
function AssignmentCard({
  meta,
  assignment,
}: {
  meta: typeof WEEK_META[0]
  assignment: Assignment | undefined
}) {
  const [expanded, setExpanded] = useState(false)
  const publishMutation = usePublishAssignment()
  const unpublishMutation = useUnpublishAssignment()
  const updateMutation = useUpdateAssignment()

  const isPublished = assignment?.is_published ?? false
  const isToggling = publishMutation.isPending || unpublishMutation.isPending

  const handleToggle = () => {
    if (!assignment) return
    if (isPublished) {
      unpublishMutation.mutate(assignment.id)
    } else {
      publishMutation.mutate(assignment.id)
    }
  }

  const handleDeadlineSave = (deadline: string) => {
    if (!assignment) return
    updateMutation.mutate({ id: assignment.id, data: { deadline } })
  }

  const Icon = meta.icon

  return (
    <div
      className={cn(
        'rounded-xl border bg-surface-main shadow-card transition-all duration-200',
        isPublished
          ? 'border-accent-teal/30'
          : 'border-navy-800'
      )}
    >
      {/* Card Header */}
      <div className="flex items-start gap-4 p-5">
        {/* Week badge + icon */}
        <div className={cn(
          'flex h-11 w-11 shrink-0 items-center justify-center rounded-xl',
          isPublished ? 'bg-accent-teal/15 text-accent-teal' : 'bg-navy-800 text-text-secondary'
        )}>
          <Icon size={20} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-0.5">
            <span className="text-[10px] font-bold uppercase tracking-widest text-text-muted">
              Week {meta.week}
            </span>
            {isPublished ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-accent-teal/10 border border-accent-teal/25 px-2 py-0.5 text-[10px] font-bold text-accent-teal">
                <CheckCircle2 size={9} /> Live
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 rounded-full bg-navy-800 border border-navy-700 px-2 py-0.5 text-[10px] font-bold text-text-muted">
                <Lock size={9} /> Draft
              </span>
            )}
          </div>

          <p className="font-display text-sm font-semibold text-text-primary truncate">{meta.title}</p>
          <p className="text-xs text-text-muted mt-0.5 truncate">{meta.subtitle}</p>
        </div>

        {/* Toggle */}
        <button
          onClick={handleToggle}
          disabled={!assignment || isToggling}
          title={isPublished ? 'Unpublish (hide from students)' : 'Publish (make live for students)'}
          className={cn(
            'shrink-0 transition-all duration-200',
            !assignment ? 'opacity-30 cursor-not-allowed' : 'cursor-pointer hover:scale-105'
          )}
        >
          {isToggling ? (
            <div className="h-8 w-14 rounded-full bg-navy-800 flex items-center justify-center">
              <div className="h-3 w-3 rounded-full border-2 border-accent-blue border-t-transparent animate-spin" />
            </div>
          ) : isPublished ? (
            <ToggleRight size={36} className="text-accent-teal drop-shadow-sm" />
          ) : (
            <ToggleLeft size={36} className="text-text-muted" />
          )}
        </button>
      </div>

      {/* Stats row */}
      <div className="px-5 pb-3 flex items-center gap-4 flex-wrap border-t border-navy-800/50 pt-3">
        {/* Deadline */}
        <div className="flex items-center gap-1.5">
          <Clock size={11} className="text-text-muted shrink-0" />
          {assignment ? (
            <DeadlineEditor
              assignment={assignment}
              onSave={handleDeadlineSave}
              isSaving={updateMutation.isPending}
            />
          ) : (
            <span className="text-xs text-text-muted italic">Loading...</span>
          )}
        </div>

        <div className="flex items-center gap-1 text-xs text-text-muted ml-auto">
          <span className="font-mono font-bold text-text-secondary">{meta.marks}</span>
          <span>pts</span>
          <span className="mx-1 text-navy-700">·</span>
          <span className="font-mono text-[11px] bg-navy-800 px-1.5 py-0.5 rounded text-text-secondary">{meta.file}</span>
        </div>

        {/* Expand */}
        <button
          onClick={() => setExpanded((v) => !v)}
          className="ml-2 flex items-center gap-1 text-[11px] text-text-muted hover:text-text-primary transition-colors"
        >
          {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>
      </div>

      {/* Expanded description */}
      {expanded && (
        <div className="px-5 pb-4 border-t border-navy-800/50 pt-3 animate-fade-in">
          <p className="text-sm text-text-secondary leading-relaxed">{meta.description}</p>
          {!assignment && (
            <p className="mt-2 text-xs text-status-warning bg-status-warning/10 border border-status-warning/20 rounded-lg px-3 py-2">
              ⚠ This assignment has not been seeded in the database yet. Run the seed script to create it.
            </p>
          )}
        </div>
      )}
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export const AssignmentManagePage = () => {
  const { data: assignments, isLoading } = useAssignments()

  // Match DB assignments to static metadata by slug
  const getAssignment = (slug: string): Assignment | undefined =>
    assignments?.find((a) => a.slug === slug)

  const publishedCount = assignments?.filter((a) => a.is_published).length ?? 0

  return (
    <PageWrapper>
      <PageHeader
        title="Assignment Management"
        description="Toggle assignments live or draft, and adjust deadlines for all 9 weeks."
      />

      {/* Summary bar */}
      <div className="mb-6 flex flex-wrap gap-3">
        <div className="flex items-center gap-2 rounded-xl border border-navy-800 bg-surface-main px-4 py-2.5 shadow-card">
          <CheckCircle2 size={14} className="text-accent-teal" />
          <span className="text-sm font-semibold text-text-primary">{publishedCount}</span>
          <span className="text-xs text-text-secondary">of 9 live</span>
        </div>
        <div className="flex items-center gap-2 rounded-xl border border-navy-800 bg-surface-main px-4 py-2.5 shadow-card">
          <Lock size={14} className="text-text-muted" />
          <span className="text-sm font-semibold text-text-primary">{9 - publishedCount}</span>
          <span className="text-xs text-text-secondary">drafts</span>
        </div>
        <div className="flex items-center gap-2 rounded-xl border border-navy-800 bg-surface-main px-4 py-2.5 shadow-card ml-auto text-xs text-text-muted">
          Click the toggle on any card to publish/unpublish. Click the deadline to edit it.
        </div>
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 9 }).map((_, i) => (
            <div key={i} className="h-32 rounded-xl border border-navy-800 bg-surface-main animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {WEEK_META.map((meta) => (
            <AssignmentCard
              key={meta.slug}
              meta={meta}
              assignment={getAssignment(meta.slug)}
            />
          ))}
        </div>
      )}
    </PageWrapper>
  )
}

export default AssignmentManagePage
