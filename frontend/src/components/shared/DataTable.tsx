import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface DataTableProps {
  headers: string[]
  rows: ReactNode[][]
  onRowClick?: (index: number) => void
  className?: string
  stickyHeader?: boolean
}

export const DataTable = ({
  headers,
  rows,
  onRowClick,
  className,
  stickyHeader = true,
}: DataTableProps) => (
  <div className={cn('overflow-hidden rounded-xl border border-navy-800', className)}>
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-left text-sm">
        <thead className={cn('bg-navy-900/80 text-text-secondary', stickyHeader && 'sticky top-0')}>
          <tr>
            {headers.map((header, i) => (
              <th
                key={i}
                className="px-4 py-3 font-medium text-xs uppercase tracking-wide"
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr
              key={rowIndex}
              className={cn(
                'border-t border-navy-800 transition-colors',
                rowIndex % 2 === 0 ? 'bg-navy-950' : 'bg-navy-900/50',
                onRowClick && 'cursor-pointer hover:bg-navy-800/40',
              )}
              onClick={() => onRowClick?.(rowIndex)}
            >
              {row.map((cell, cellIndex) => (
                <td key={cellIndex} className="px-4 py-3 text-text-primary">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length === 0 && (
        <div className="py-10 text-center text-sm text-text-secondary">
          No data to display.
        </div>
      )}
    </div>
  </div>
)
