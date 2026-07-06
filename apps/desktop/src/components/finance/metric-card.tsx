import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatINR } from '@/lib/utils'

interface MetricCardProps {
  title: string
  value: string
  subtitle?: string
  tone?: 'default' | 'positive' | 'negative' | 'warning'
}

const toneClass: Record<NonNullable<MetricCardProps['tone']>, string> = {
  default: 'text-foreground',
  positive: 'text-emerald-400',
  negative: 'text-rose-400',
  warning: 'text-amber-400',
}

export function MetricCard({ title, value, subtitle, tone = 'default' }: MetricCardProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className={`text-2xl font-semibold ${toneClass[tone]}`}>{value}</p>
        {subtitle ? <p className="mt-1 text-xs text-muted-foreground">{subtitle}</p> : null}
      </CardContent>
    </Card>
  )
}

export function UtilizationBar({ percent }: { percent: number }) {
  const clamped = Math.min(Math.max(percent, 0), 100)
  const tone = clamped >= 80 ? 'bg-rose-500' : clamped >= 50 ? 'bg-amber-500' : 'bg-emerald-500'
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>Utilization</span>
        <span>{clamped.toFixed(1)}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-muted">
        <div className={`h-full rounded-full transition-all ${tone}`} style={{ width: `${clamped}%` }} />
      </div>
    </div>
  )
}

export function Amount({ value, direction }: { value: number; direction?: string }) {
  const tone =
    direction === 'debit' || direction === 'expense'
      ? 'text-rose-400'
      : direction === 'credit' || direction === 'income'
        ? 'text-emerald-400'
        : 'text-foreground'
  return <span className={`font-medium ${tone}`}>{formatINR(value)}</span>
}
