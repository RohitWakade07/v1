interface RecentActivityFeedProps {
  items: { label: string; detail: string }[]
}

export const RecentActivityFeed = ({ items }: RecentActivityFeedProps) => (
  <div className="rounded-xl border border-navy-800 bg-navy-900/50 p-5 shadow-card">
    <h3 className="font-display text-lg font-semibold text-text-primary">
      Recent Activity
    </h3>
    <div className="mt-4 space-y-3">
      {items.map((item, index) => (
        <div key={`${item.label}-${index}`}>
          <p className="text-sm text-text-primary">{item.label}</p>
          <p className="text-xs text-text-secondary">{item.detail}</p>
        </div>
      ))}
    </div>
  </div>
)
