interface PageHeaderProps {
  title: string
  description?: string
  actions?: React.ReactNode
}

export const PageHeader = ({ title, description, actions }: PageHeaderProps) => (
  <div className="mb-6 flex items-start justify-between animate-fade-in-up">
    <div>
      <h1 className="font-display text-2xl font-bold text-text-primary">{title}</h1>
      {description && <p className="mt-1 text-sm text-text-secondary">{description}</p>}
    </div>
    {actions && <div className="flex items-center gap-3">{actions}</div>}
  </div>
)
