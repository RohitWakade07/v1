import { Download } from 'lucide-react'

interface CertificateDownloadButtonProps {
  disabled?: boolean
}

export const CertificateDownloadButton = ({
  disabled = true,
}: CertificateDownloadButtonProps) => (
  <button
    type="button"
    className="inline-flex items-center gap-2 rounded-lg border border-navy-800 bg-navy-900 px-4 py-2 text-sm text-text-secondary"
    disabled={disabled}
    title={disabled ? 'Certificate generation coming in Phase 2' : 'Download'}
  >
    <Download size={16} />
    Download Certificate
  </button>
)
