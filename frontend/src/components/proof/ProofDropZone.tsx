import { FileCheck2, CheckCircle2, UploadCloud } from 'lucide-react'
import { useCallback, useState } from 'react'
import { cn } from '@/lib/utils'

interface ProofDropZoneProps {
  onFileSelected: (file: File) => void
  fileName?: string
  hasError?: boolean
}

export const ProofDropZone = ({ onFileSelected, fileName, hasError }: ProofDropZoneProps) => {
  const [dragActive, setDragActive] = useState(false)

  const onDrop = useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      event.preventDefault()
      setDragActive(false)
      const file = event.dataTransfer.files?.[0]
      if (file) onFileSelected(file)
    },
    [onFileSelected],
  )

  const hasFile = Boolean(fileName)

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label="Drop proof.json file here or click to browse"
      className={cn(
        'relative flex flex-col items-center gap-4 rounded-xl border-2 border-dashed px-8 py-12 text-center transition-all duration-200',
        dragActive
          ? 'border-accent-blue bg-accent-blue/10'
          : hasFile
          ? 'border-accent-teal/50 bg-accent-teal/5'
          : hasError
          ? 'border-status-danger/50 bg-status-danger/5'
          : 'border-navy-800 bg-navy-900/40 hover:border-accent-blue/50 hover:bg-navy-900/60',
      )}
      onDragOver={(e) => { e.preventDefault(); setDragActive(true) }}
      onDragLeave={() => setDragActive(false)}
      onDrop={onDrop}
    >
      {/* Icon */}
      <div className={cn(
        'flex h-14 w-14 items-center justify-center rounded-full transition-colors',
        hasFile ? 'bg-accent-teal/15 text-accent-teal' : 'bg-accent-blue/15 text-accent-blue',
      )}>
        {hasFile ? <CheckCircle2 size={28} /> : dragActive ? <UploadCloud size={28} className="animate-bounce" /> : <FileCheck2 size={28} />}
      </div>

      {/* Text */}
      {hasFile ? (
        <div>
          <p className="font-medium text-accent-teal">File loaded successfully</p>
          <p className="mt-1 font-mono text-xs text-text-secondary">{fileName}</p>
          <p className="mt-2 text-xs text-text-secondary">Drop a different file to replace</p>
        </div>
      ) : (
        <div>
          <p className="font-medium text-text-primary">Drop your proof.json file here</p>
          <p className="mt-1 text-sm text-text-secondary">or click the button below to browse</p>
          <p className="mt-2 text-xs text-text-secondary">JSON format, max 5 MB</p>
        </div>
      )}

      {/* Browse button */}
      <label className="btn-secondary cursor-pointer text-sm">
        Browse file
        <input
          type="file"
          accept="application/json,.json"
          className="sr-only"
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) onFileSelected(file)
            e.target.value = ''
          }}
        />
      </label>
    </div>
  )
}
