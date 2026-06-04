import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-lg text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-blue/60 disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-accent-blue text-white hover:bg-[#2471A3]',
        secondary: 'border border-accent-blue text-accent-blue hover:bg-accent-blue/10',
        destructive: 'bg-status-danger text-white hover:bg-status-danger/90',
        ghost: 'text-text-secondary hover:bg-navy-800/40 hover:text-text-primary',
      },
      size: {
        default: 'px-4 py-2',
        sm: 'px-3 py-1.5 text-xs',
        lg: 'px-5 py-2.5',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button
      ref={ref}
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  ),
)

Button.displayName = 'Button'

export { Button }
