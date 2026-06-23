import { Timer, Award, BookOpen } from 'lucide-react'
import type { AssignmentDetail } from '@/types/api'
import { CategoryBadge } from '@/components/shared/StatusBadge'
import { formatDate, formatRelative } from '@/lib/utils'
import { cn } from '@/lib/utils'


interface TreeNode {
  name: string;
  children: Record<string, TreeNode>;
  isFile: boolean;
}

const buildTree = (paths: string[]) => {
  const root: TreeNode = { name: 'root', children: {}, isFile: false };
  paths.forEach(path => {
    const parts = path.split('/').filter(Boolean);
    let current = root;
    parts.forEach((part, i) => {
      if (!current.children[part]) {
        current.children[part] = {
          name: part,
          children: {},
          isFile: i === parts.length - 1 && !path.endsWith('/')
        };
      }
      current = current.children[part];
    });
  });
  return root;
};

const renderTreeNodes = (node: TreeNode, depth = 0, isLast = true, prefix = '') => {
  const entries = Object.values(node.children);
  return entries.map((child, idx) => {
    const isChildLast = idx === entries.length - 1;
    const branch = depth === 0 ? '' : (isChildLast ? '└── ' : '├── ');
    
    return (
      <div key={child.name + depth + idx}>
        <div className="flex items-center gap-2 font-mono text-sm text-text-primary" style={{ paddingLeft: depth === 0 ? 0 : '0.5rem' }}>
          {depth > 0 && <span className="text-navy-500 whitespace-pre">{prefix + branch}</span>}
          <span className={child.isFile ? "text-accent-teal" : "text-accent-blue"}>
            {child.isFile ? '📄' : '📦'}
          </span>
          <span>{child.name}</span>
        </div>
        {Object.keys(child.children).length > 0 && (
          <div className="flex flex-col">
            {renderTreeNodes(child, depth + 1, isChildLast, depth === 0 ? '' : prefix + (isChildLast ? '    ' : '│   '))}
          </div>
        )}
      </div>
    );
  });
};

const isUrgent = (deadline?: string) => {
  if (!deadline) return false
  return new Date(deadline).getTime() - Date.now() < 48 * 3600 * 1000
}

interface AssignmentDetailPanelProps {
  assignment: AssignmentDetail
}

export const AssignmentDetailPanel = ({ assignment }: AssignmentDetailPanelProps) => {
  const urgent = isUrgent(assignment.deadline)
  const resourceLinks = Array.isArray(assignment.resource_links)
    ? assignment.resource_links
    : []

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
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <p className="text-xs text-text-muted">
              Deadline: {formatDate(assignment.deadline)}
            </p>
            {assignment.allow_late_submissions && assignment.late_penalty_pct ? (
              <span className="rounded bg-status-warning/10 px-2 py-0.5 text-[10px] font-semibold text-status-warning border border-status-warning/20">
                Late submissions allowed (-{assignment.late_penalty_pct}% penalty)
              </span>
            ) : null}
          </div>
        )}
      </div>

      <div className="rounded-xl border border-navy-800 bg-surface-main p-6 shadow-card">
        <div className="mb-4 flex items-center gap-2">
          <BookOpen size={16} className="text-accent-blue" />
          <h3 className="font-display text-base font-semibold text-text-primary">Submission Instructions</h3>
        </div>
        
        {(() => {
          // Use DB-stored submission_filename if set, else fall back to slug-based defaults
          let filename = assignment.submission_filename || ''
          let isRepo = false
          if (!filename) {
            if (assignment.slug === 'week1') filename = 'commands.txt'
            else if (assignment.slug === 'week2') filename = 'analyze.sh'
            else if (assignment.slug === 'week3') filename = 'organize.sh'
            else if (assignment.slug === 'week4') { filename = 'RECOVERY.md'; isRepo = true }
            else filename = 'your_script.sh'
          }
          if (filename === 'RECOVERY.md') isRepo = true

          return (
            <div className="rounded-xl border border-accent-blue/20 bg-accent-blue/5 overflow-hidden">
              <div className="bg-accent-blue/10 px-5 py-3 border-b border-accent-blue/20 flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-accent-blue animate-pulse" />
                <h3 className="font-display text-sm font-semibold text-accent-blue">Required Submission Format</h3>
              </div>
              
              {/* Custom instructions from admin or default steps */}
              {assignment.submission_instructions ? (
                <div className="p-5">
                  <p className="text-sm text-text-secondary leading-relaxed whitespace-pre-wrap">
                    {assignment.submission_instructions}
                  </p>
                </div>
              ) : (
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
                    
                    {assignment.expected_media_url && (
                      <div className="mb-4 rounded-lg overflow-hidden border border-navy-700">
                        <img src={assignment.expected_media_url} alt="Expected Structure" className="w-full object-contain bg-navy-900" />
                      </div>
                    )}

                    {assignment.expected_structure ? (
                      <div className="file-tree-block p-4 rounded-lg bg-navy-900 border border-navy-800 overflow-x-auto">
                        {renderTreeNodes(buildTree(assignment.expected_structure.split('
').map(p => p.trim()).filter(Boolean)))}
                      </div>
                    ) : (
                      <div className="file-tree-block">
                        <div className="tree-root flex items-center gap-2 mb-1">
                          <span className="text-accent-blue">📦</span> submission.zip
                        </div>
                        {isRepo ? (
                          <>
                            <div className="tree-leaf flex items-center gap-2 ml-1">
                              <span className="tree-branch">├──</span> 
                              <span className="text-accent-blue">📦</span> .git/
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
                    )}
                  </div>
                </div>
              )}
              )}
            </div>
          )
        })()}
      </div>


      {resourceLinks.length > 0 && (
        <div className="rounded-xl border border-navy-800 bg-surface-main p-6 shadow-card">
          <h3 className="font-display text-base font-semibold text-text-primary mb-4 flex items-center gap-2">
            📎 Resources
          </h3>
          <div className="space-y-3">
            {resourceLinks.map((link: { url: string; title: string; type?: string }, i: number) => {
              const isVideo = link.type === 'video' || link.url?.includes('youtube') || link.url?.includes('youtu.be') || link.url?.includes('vimeo')
              const isImage = link.type === 'image' || link.url?.match(/\.(png|jpg|jpeg|gif|webp|svg)(\?|$)/i)

              const getYoutubeId = (url: string) => {
                const m = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\s]+)/)
                return m ? m[1] : null
              }

              if (isVideo) {
                const ytId = getYoutubeId(link.url || '')
                return (
                  <div key={i} className="rounded-lg border border-red-400/20 bg-red-400/5 overflow-hidden">
                    <div className="flex items-center gap-2 px-3 py-2 border-b border-red-400/20">
                      <span className="text-[10px] font-bold text-red-400 border border-red-400/30 px-1.5 py-0.5 rounded">▶ VIDEO</span>
                      <span className="text-sm font-medium text-text-primary">{link.title}</span>
                    </div>
                    {ytId ? (
                      <div className="aspect-video">
                        <iframe
                          src={`https://www.youtube.com/embed/${ytId}`}
                          className="w-full h-full"
                          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                          allowFullScreen
                        />
                      </div>
                    ) : (
                      <a href={link.url} target="_blank" rel="noreferrer"
                        className="block p-3 text-xs text-text-secondary hover:text-red-400 truncate transition-colors">
                        {link.url}
                      </a>
                    )}
                  </div>
                )
              }

              if (isImage) {
                return (
                  <div key={i} className="rounded-lg border border-purple-400/20 bg-purple-400/5 overflow-hidden">
                    <div className="flex items-center gap-2 px-3 py-2 border-b border-purple-400/20">
                      <span className="text-[10px] font-bold text-purple-400 border border-purple-400/30 px-1.5 py-0.5 rounded">🖼 IMAGE</span>
                      <span className="text-sm font-medium text-text-primary">{link.title}</span>
                    </div>
                    <a href={link.url} target="_blank" rel="noreferrer">
                      <img src={link.url} alt={link.title}
                        className="w-full max-h-64 object-contain bg-navy-950 p-2 hover:opacity-90 transition-opacity" />
                    </a>
                  </div>
                )
              }

              return (
                <a
                  key={i}
                  href={link.url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-3 rounded-lg border border-navy-700 bg-navy-800/40 p-3 hover:border-accent-blue/40 hover:bg-navy-800 transition-colors group"
                >
                  <span className="text-[10px] font-bold text-accent-blue border border-accent-blue/30 px-1.5 py-0.5 rounded bg-accent-blue/10 shrink-0">🔗 LINK</span>
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-medium text-text-primary group-hover:text-accent-blue transition-colors">{link.title}</div>
                    <div className="mt-0.5 text-xs text-text-secondary truncate">{link.url}</div>
                  </div>
                </a>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
