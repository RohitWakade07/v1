import { FileCheck2 } from 'lucide-react'
import { useCallback, useState } from 'react'
import { cn } from '@/lib/utils'

interface ProofDropZoneProps {
  onFileSelected: (file: File) => void
  fileName?: string
}

export const ProofDropZone = ({ onFileSelected, fileName }: ProofDropZoneProps) => {
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

  return (
    <div
      className={cn(
        'flex flex-col items-center gap-3 rounded-xl border-2 border-dashed border-navy-800 bg-navy-900/40 px-6 py-10 text-center',
        dragActive && 'border-accent-blue/60 bg-navy-900/70',
      )}
      onDragOver={(event) => {
        event.preventDefault()
        setDragActive(true)
      }}
      onDragLeave={() => setDragActive(false)}
      onDrop={onDrop}
    >
      <FileCheck2 size={28} className="text-accent-blue" />
      <div>
        <p className="font-medium text-text-primary">
          Drop your proof.json file here
        </p>
        <p className="text-sm text-text-secondary">
          or click to browse from your device
        </p>
      </div>
      <label className="mt-2 cursor-pointer rounded-lg border border-accent-blue px-4 py-2 text-sm font-medium text-accent-blue">
        Browse file
        <input
          type="file"
          accept="application/json"
          className="hidden"
          onChange={(event) => {
            const file = event.target.files?.[0]
            if (file) onFileSelected(file)
          }}
        />
      </label>
      {fileName && (
        <p className="text-xs text-text-secondary">Selected: {fileName}</p>
      )}
    </div>
  )
}
