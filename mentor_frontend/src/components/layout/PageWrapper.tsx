import type { ReactNode } from 'react'

interface PageWrapperProps {
  children: ReactNode
}

export const PageWrapper = ({ children }: PageWrapperProps) => {
  return (
    <div className="flex flex-col gap-6">{children}</div>
  )
}
