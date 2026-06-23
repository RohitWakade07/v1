import React, { useState, useRef } from 'react'
import { FileArchive, GitBranch, UploadCloud, Loader2 } from 'lucide-react'
import type { SubmissionSourceType } from '@/types/api'

interface SubmissionFormProps {
  onSubmit: (sourceType: SubmissionSourceType, repoUrl?: string, file?: File) => void
  isSubmitting: boolean
  maxFileSizeMB?: number
}

export const SubmissionForm: React.FC<SubmissionFormProps> = ({
  onSubmit,
  isSubmitting,
  maxFileSizeMB = 5,
}) => {
  const [sourceType, setSourceType] = useState<SubmissionSourceType>('github')
  const [repoUrl, setRepoUrl] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    setError(null)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault()
    setError(null)
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }

  const handleFile = (selectedFile: File) => {
    if (selectedFile.size > maxFileSizeMB * 1024 * 1024) {
      setError(`File exceeds the ${maxFileSizeMB}MB limit.`)
      setFile(null)
      return
    }
    if (!selectedFile.name.endsWith('.zip')) {
      setError('Only .zip files are allowed.')
      setFile(null)
      return
    }
    setFile(selectedFile)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    
    if (sourceType === 'github') {
      if (!repoUrl.trim()) {
        setError('GitHub Repository URL is required.')
        return
      }
      try {
        new URL(repoUrl)
      } catch {
        setError('Please enter a valid URL.')
        return
      }
      onSubmit('github', repoUrl, undefined)
    } else {
      if (!file) {
        setError('Please select a ZIP file.')
        return
      }
      onSubmit('zip', undefined, file)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex bg-navy-900 rounded-lg p-1">
        <button
          type="button"
          onClick={() => {
            setSourceType('github')
            setError(null)
          }}
          className={`flex-1 flex items-center justify-center gap-2 py-2 text-sm font-semibold rounded-md transition-colors ${
            sourceType === 'github'
              ? 'bg-accent-blue text-white shadow'
              : 'text-text-secondary hover:text-text-primary'
          }`}
        >
          <GitBranch size={16} />
          GitHub Repository
        </button>
        <button
          type="button"
          onClick={() => {
            setSourceType('zip')
            setError(null)
          }}
          className={`flex-1 flex items-center justify-center gap-2 py-2 text-sm font-semibold rounded-md transition-colors ${
            sourceType === 'zip'
              ? 'bg-accent-blue text-white shadow'
              : 'text-text-secondary hover:text-text-primary'
          }`}
        >
          <FileArchive size={16} />
          ZIP Upload
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {sourceType === 'github' && (
          <div className="animate-fade-in space-y-2">
            <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider">
              Repository URL
            </label>
            <input
              type="text"
              placeholder="https://github.com/username/repository"
              className="input-dark w-full"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              disabled={isSubmitting}
            />
            <p className="text-[10px] text-text-muted">
              Provide a public GitHub repository link. The backend will perform a shallow clone.
            </p>
          </div>
        )}

        {sourceType === 'zip' && (
          <div className="animate-fade-in space-y-2">
            <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider">
              Upload Archive
            </label>
            <div
              className={`relative border-2 border-dashed rounded-xl p-6 text-center transition-colors ${
                dragActive
                  ? 'border-accent-blue bg-accent-blue/5'
                  : 'border-navy-700 bg-navy-900 hover:border-navy-600'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <input
                ref={inputRef}
                type="file"
                accept=".zip"
                onChange={handleChange}
                className="hidden"
                disabled={isSubmitting}
              />
              <UploadCloud
                size={32}
                className={`mx-auto mb-3 ${dragActive ? 'text-accent-blue' : 'text-text-muted'}`}
              />
              {file ? (
                <div>
                  <p className="text-sm font-semibold text-text-primary">{file.name}</p>
                  <p className="text-xs text-text-muted mt-1">
                    {file.size < 1024 * 1024 
                      ? `${Math.max(1, Math.round(file.size / 1024))} KB` 
                      : `${(file.size / 1024 / 1024).toFixed(2)} MB`}
                  </p>
                  <button
                    type="button"
                    onClick={() => setFile(null)}
                    className="text-xs text-status-danger hover:underline mt-2"
                    disabled={isSubmitting}
                  >
                    Remove
                  </button>
                </div>
              ) : (
                <div>
                  <p className="text-sm text-text-secondary">
                    Drag and drop your ZIP archive here, or{' '}
                    <button
                      type="button"
                      onClick={() => inputRef.current?.click()}
                      className="text-accent-blue hover:underline focus:outline-none"
                    >
                      browse
                    </button>
                  </p>
                  <p className="text-[10px] text-text-muted mt-2">
                    Must be a .zip file (Max {maxFileSizeMB}MB).
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {error && (
          <div className="text-sm text-status-danger bg-status-danger/10 p-3 rounded-lg border border-status-danger/20">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={isSubmitting || (sourceType === 'zip' && !file) || (sourceType === 'github' && !repoUrl)}
          className="btn-primary w-full justify-center"
        >
          {isSubmitting ? (
            <>
              <Loader2 size={16} className="animate-spin mr-2" />
              Submitting...
            </>
          ) : (
            'Submit Assignment'
          )}
        </button>
      </form>
    </div>
  )
}
