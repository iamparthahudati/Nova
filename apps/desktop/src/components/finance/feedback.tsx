import { AlertCircle, CheckCircle2 } from 'lucide-react'
import type { FinanceFeedback } from '@/hooks/use-finance-feedback'
import { cn } from '@/lib/utils'

export function FeedbackBanner({
  feedback,
  className,
}: {
  feedback: FinanceFeedback | null
  className?: string
}) {
  if (!feedback) return null
  const isError = feedback.tone === 'error'
  const Icon = isError ? AlertCircle : CheckCircle2
  return (
    <div
      role={isError ? 'alert' : 'status'}
      aria-live={isError ? 'assertive' : 'polite'}
      className={cn(
        'mb-4 flex items-start gap-2 rounded-md border p-3 text-sm',
        isError
          ? 'border-destructive/30 bg-destructive/10 text-destructive'
          : 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
        className,
      )}
    >
      <Icon className="mt-0.5 size-4 shrink-0" />
      <p>{feedback.message}</p>
    </div>
  )
}
