import { Link } from 'react-router-dom'
import { ArrowRight, Building2, Clock } from 'lucide-react'
import { RewardStatusChip } from '@/components/finance/reward-status-chip'
import { Card, CardContent } from '@/components/ui/card'
import { formatRewardUnit, programBalanceDisplay } from '@/lib/finance/reward-display'
import { cn } from '@/lib/utils'
import type { RewardProgram } from '@/view-models/finance'

interface RewardProgramCardProps {
  program: RewardProgram
  selected?: boolean
  onSelect?: () => void
}

export function RewardProgramCard({ program, selected, onSelect }: RewardProgramCardProps) {
  const status = program.status ?? 'new'

  return (
    <Card
      className={cn(
        'transition hover:border-emerald-500/30',
        selected && 'border-emerald-500/50 ring-1 ring-emerald-500/20',
      )}
    >
      <CardContent className="space-y-4 p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="truncate font-semibold">{program.name}</p>
            <p className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground">
              <Building2 className="size-3.5 shrink-0" />
              <span className="truncate">{program.bankName ?? program.accountName ?? 'Credit card'}</span>
            </p>
          </div>
          <RewardStatusChip status={status} />
        </div>

        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-xs text-muted-foreground">Balance</p>
            <p className="mt-0.5 text-lg font-semibold text-emerald-400">{programBalanceDisplay(program)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Unit</p>
            <p className="mt-0.5 font-medium">{formatRewardUnit(program.unit)}</p>
          </div>
        </div>

        {program.expiryNote ? (
          <p className="flex items-start gap-1.5 text-xs text-muted-foreground">
            <Clock className="mt-0.5 size-3.5 shrink-0 text-amber-400" />
            <span>{program.expiryNote}</span>
          </p>
        ) : null}

        <div className="flex items-center justify-between gap-2 pt-1">
          <button
            type="button"
            className="text-xs font-medium text-muted-foreground hover:text-foreground"
            onClick={onSelect}
          >
            View ledger
          </button>
          <Link
            to={`/finance/rewards/${program.id}`}
            className="inline-flex items-center gap-1 text-xs font-medium text-emerald-400 hover:underline"
          >
            Details
            <ArrowRight className="size-3" />
          </Link>
        </div>
      </CardContent>
    </Card>
  )
}
