export const SkeletonCard = () => (
  <div className="card-dark p-5 space-y-3">
    <div className="skeleton h-4 w-1/3" />
    <div className="skeleton h-8 w-1/2" />
    <div className="skeleton h-3 w-2/3" />
  </div>
)

export const SkeletonStatCard = () => (
  <div className="card-dark p-5 flex items-start justify-between">
    <div className="space-y-2">
      <div className="skeleton h-3 w-24" />
      <div className="skeleton h-8 w-16" />
      <div className="skeleton h-3 w-32" />
    </div>
    <div className="skeleton h-12 w-12 rounded-xl" />
  </div>
)

export const SkeletonRow = () => (
  <tr>
    {Array.from({ length: 5 }).map((_, i) => (
      <td key={i} className="px-4 py-3">
        <div className="skeleton h-4 w-full" />
      </td>
    ))}
  </tr>
)
