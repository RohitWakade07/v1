import { FileCheck2, CheckCircle2, UploadCloud, Lock } from 'lucide-react'
import { useCallback, useState } from 'react'
import { cn } from '@/lib/utils'

const EEP_EXTENSIONS = ['.eep1', '.eep2', '.eep3']

export function isEepProofFile(file: File): boolean {
  const name = file.name.toLowerCase()
  return EEP_EXTENSIONS.some((ext) => name.endsWith(ext))
}

interface ProofDropZoneProps {
  onFileSelected: (file: File, isEepFile: boolean) => void
  fileName?: string
  isEepFile?: boolean
  fileSize?: number
  hasError?: boolean
}

export const ProofDropZone = ({
  onFileSelected,
  fileName,
  isEepFile = false,
  fileSize,
  hasError,
}: ProofDropZoneProps) => {
  const [dragActive, setDragActive] = useState(false)

  const handleFile = useCallback(
    (file: File) => {
      onFileSelected(file, isEepProofFile(file))
    },
    [onFileSelected],
  )

  const onDrop = useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      event.preventDefault()
      setDragActive(false)
      const file = event.dataTransfer.files?.[0]
      if (file) handleFile(file)
    },
    [handleFile],
  )

  const hasFile = Boolean(fileName)
  const acceptTypes =
    'application/json,.json,application/octet-stream,.eep1,.eep2,.eep3'

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label="Drop proof.json or EEP file here or click to browse"
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
      <div className={cn(
        'flex h-14 w-14 items-center justify-center rounded-full transition-colors',
        hasFile ? 'bg-accent-teal/15 text-accent-teal' : 'bg-accent-blue/15 text-accent-blue',
      )}>
        {hasFile ? (
          isEepFile ? <Lock size={28} /> : <CheckCircle2 size={28} />
        ) : dragActive ? (
          <UploadCloud size={28} className="animate-bounce" />
        ) : (
          <FileCheck2 size={28} />
        )}
      </div>

      {hasFile ? (
        <div>
          <p className="font-medium text-accent-teal">File loaded successfully</p>
          <p className="mt-1 font-mono text-xs text-text-secondary">{fileName}</p>
          {fileSize !== undefined && (
            <p className="mt-1 text-xs text-text-muted">
              {(fileSize / 1024).toFixed(1)} KB
            </p>
          )}
          {isEepFile && (
            <p className="mt-2 text-xs text-text-secondary">
              Encrypted EEP submission — contents verified server-side
            </p>
          )}
          <p className="mt-2 text-xs text-text-secondary">Drop a different file to replace</p>
        </div>
      ) : (
        <div>
          <p className="font-medium text-text-primary">
            Drop your proof.json or .eep1/.eep2/.eep3 file here
          </p>
          <p className="mt-1 text-sm text-text-secondary">or click the button below to browse</p>
          <p className="mt-2 text-xs text-text-secondary">JSON or EEP encrypted proof, max 5 MB</p>
        </div>
      )}

      <label className="btn-secondary cursor-pointer text-sm">
        Browse file
        <input
          type="file"
          accept={acceptTypes}
          className="sr-only"
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) handleFile(file)
            e.target.value = ''
          }}
        />
      </label>
    </div>
  )
}
