import { Timer, Award, Download, BookOpen } from 'lucide-react'
import type { AssignmentDetail } from '@/types/api'
import { CategoryBadge } from '@/components/shared/StatusBadge'
import { formatDate, formatRelative } from '@/lib/utils'
import { cn } from '@/lib/utils'

const isUrgent = (deadline?: string) => {
  if (!deadline) return false
  return new Date(deadline).getTime() - Date.now() < 48 * 3600 * 1000
}

interface AssignmentDetailPanelProps {
  assignment: AssignmentDetail
}

export const AssignmentDetailPanel = ({ assignment }: AssignmentDetailPanelProps) => {
  const urgent = isUrgent(assignment.deadline)

  return (
    <div className="space-y-5">
      <div className="rounded-xl border border-navy-800 bg-surface-main p-6 shadow-card">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <CategoryBadge category={assignment.category} />
            <h2 className="mt-2 font-display text-2xl font-bold text-text-primary">
              {assignment.title}
            </h2>
          </div>
          <div className="flex flex-wrap gap-2">
            <span className={cn(
              'inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold',
              urgent
                ? 'bg-status-warning/15 text-status-warning border border-status-warning/30'
                : 'bg-navy-800/60 text-text-secondary border border-navy-800',
            )}>
              <Timer size={11} />
              {assignment.deadline ? (urgent ? `⚠ ${formatRelative(assignment.deadline)}` : formatRelative(assignment.deadline)) : 'No deadline'}
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-navy-800/60 border border-navy-800 px-3 py-1 text-xs font-semibold text-text-secondary">
              <Award size={11} />
              {assignment.max_score} pts max
            </span>
          </div>
        </div>

        <p className="mt-4 text-sm leading-relaxed text-text-secondary">
          {assignment.description || 'No description provided for this assignment.'}
        </p>

        {assignment.deadline && (
          <p className="mt-3 text-xs text-text-muted">
            Deadline: {formatDate(assignment.deadline)}
          </p>
        )}
      </div>

      <div className="rounded-xl border border-navy-800 bg-surface-main p-6 shadow-card">
        <div className="mb-4 flex items-center gap-2">
          <BookOpen size={16} className="text-accent-blue" />
          <h3 className="font-display text-base font-semibold text-text-primary">Submission Instructions</h3>
        </div>
        
        {(() => {
          // Determine expected filename based on assignment slug
          let filename = 'your_script.sh'
          let isRepo = false
          if (assignment.slug === 'week1') filename = 'commands.txt'
          else if (assignment.slug === 'week2') filename = 'analyze.sh'
          else if (assignment.slug === 'week3') filename = 'organize.sh'
          else if (assignment.slug === 'week4') { filename = 'RECOVERY.md'; isRepo = true }

          return (
            <div className="rounded-xl border border-accent-blue/20 bg-accent-blue/5 overflow-hidden">
              <div className="bg-accent-blue/10 px-5 py-3 border-b border-accent-blue/20 flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-accent-blue animate-pulse" />
                <h3 className="font-display text-sm font-semibold text-accent-blue">Required Submission Format</h3>
              </div>
              
              <div className="p-5 grid gap-6 md:grid-cols-2">
                <div className="space-y-4">
                  <p className="text-sm text-text-primary font-medium">Please follow these exact steps:</p>
                  <ul className="space-y-3">
                    <li className="flex items-start gap-3 text-sm text-text-secondary">
                      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-navy-800 text-[10px] font-bold text-text-primary border border-navy-700">1</span>
                      <span>Ensure your {isRepo ? 'repository contains' : 'file is exactly named'} <code className="rounded bg-navy-900 px-1.5 py-0.5 text-accent-teal font-mono">{filename}</code></span>
                    </li>
                    <li className="flex items-start gap-3 text-sm text-text-secondary">
                      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-navy-800 text-[10px] font-bold text-text-primary border border-navy-700">2</span>
                      <span>{isRepo ? 'Ensure the hidden .git directory is included' : 'Do not place the file inside any folders'}</span>
                    </li>
                    <li className="flex items-start gap-3 text-sm text-text-secondary">
                      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-navy-800 text-[10px] font-bold text-text-primary border border-navy-700">3</span>
                      <span>Select the {isRepo ? 'repository folder or files' : 'file directly'}, right-click, and compress into a <code className="rounded bg-navy-900 px-1.5 py-0.5 text-accent-blue font-mono">.zip</code> archive</span>
                    </li>
                    <li className="flex items-start gap-3 text-sm text-text-secondary">
                      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-navy-800 text-[10px] font-bold text-text-primary border border-navy-700">4</span>
                      <span>Upload the resulting zip file here</span>
                    </li>
                  </ul>
                </div>

                <div className="space-y-3">
                  <p className="text-sm text-text-primary font-medium">Expected ZIP Structure:</p>
                  <div className="file-tree-block">
                    <div className="tree-root flex items-center gap-2 mb-1">
                      <span className="text-accent-blue">📦</span> submission.zip
                    </div>
                    {isRepo ? (
                      <>
                        <div className="tree-leaf flex items-center gap-2 ml-1">
                          <span className="tree-branch">├──</span> 
                          <span className="text-accent-blue">📁</span> .git/
                        </div>
                        <div className="tree-leaf flex items-center gap-2 ml-1">
                          <span className="tree-branch">├──</span> 
                          <span className="text-accent-teal">📄</span> .gitignore
                        </div>
                        <div className="tree-leaf flex items-center gap-2 ml-1">
                          <span className="tree-branch">└──</span> 
                          <span className="text-accent-teal">📄</span> {filename}
                        </div>
                      </>
                    ) : (
                      <div className="tree-leaf flex items-center gap-2 ml-1">
                        <span className="tree-branch">└──</span> 
                        <span className="text-accent-teal">📄</span> {filename}
                      </div>
                    )}
                  </div>
                </div>
              </div>
              
              {assignment.instructions && (
                <div className="px-5 py-4 bg-surface-inset border-t border-navy-800">
                  <h4 className="text-xs font-bold text-text-secondary uppercase tracking-wider mb-2">Evaluator Details</h4>
                  <p className="text-sm text-text-secondary leading-relaxed">{assignment.instructions}</p>
                </div>
              )}
            </div>
          )
        })()}
      </div>

      <div className="flex items-center gap-4 rounded-xl border border-navy-800 bg-navy-900/50 p-5">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent-blue/15 text-accent-blue">
          <Download size={18} />
        </div>
        <div>
          <p className="text-sm font-semibold text-text-primary">Evaluator Binary</p>
          <p className="mt-0.5 text-xs text-text-secondary">
            Evaluator available — check your programme resources or contact your mentor to obtain the evaluator package.
          </p>
        </div>
      </div>
    </div>
  )
}
