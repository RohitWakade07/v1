import type { ReactNode } from 'react'

interface DataTableProps {
  headers: string[]
  rows: ReactNode[][]
}

export const DataTable = ({ headers, rows }: DataTableProps) => {
  return (
    <div className="overflow-hidden rounded-xl border border-navy-800">
      <table className="w-full border-collapse text-left text-sm">
        <thead className="bg-navy-900 text-text-secondary">
          <tr>
            {headers.map((header) => (
              <th key={header} className="px-4 py-3 font-medium">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr
              key={`row-${rowIndex}`}
              className="border-t border-navy-800 bg-navy-950/70 text-text-primary transition hover:bg-navy-900/60"
            >
              {row.map((cell, cellIndex) => (
                <td key={`cell-${rowIndex}-${cellIndex}`} className="px-4 py-3">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
