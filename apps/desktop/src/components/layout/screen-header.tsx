import type { ReactNode } from 'react'

interface ScreenHeaderProps {
  title: string
  description: string
  actions?: ReactNode
}

export function ScreenHeader({ title, description, actions }: ScreenHeaderProps) {
  return (
    <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{description}</p>
      </div>
      {actions}
    </div>
  )
}
