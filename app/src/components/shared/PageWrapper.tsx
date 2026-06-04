import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface PageWrapperProps { children: ReactNode; className?: string }
export const PageWrapper = ({ children, className }: PageWrapperProps) => (
  <div className={cn('mx-auto max-w-7xl animate-fade-in-up p-6', className)}>
    {children}
  </div>
)
