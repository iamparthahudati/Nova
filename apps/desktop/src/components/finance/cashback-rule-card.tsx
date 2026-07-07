import { Link } from 'react-router-dom'
import { ArrowRight, Building2, CreditCard } from 'lucide-react'
import { CashbackStatusChip } from '@/components/finance/cashback-status-chip'
import { Card, CardContent } from '@/components/ui/card'
import { formatMultiplierMap } from '@/lib/finance/cashback-display'
import { cn, formatINR } from '@/lib/utils'
import type { CashbackRule } from '@/view-models/finance'

interface CashbackRuleCardProps {
  rule: CashbackRule
  selected?: boolean
  onSelect?: () => void
}

export function CashbackRuleCard({ rule, selected, onSelect }: CashbackRuleCardProps) {
  const status = rule.status ?? 'active'

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
            <p className="truncate font-semibold">{rule.name}</p>
            <p className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground">
              <Building2 className="size-3.5 shrink-0" />
              <span className="truncate">{rule.cardName ?? rule.programName ?? 'Credit card'}</span>
            </p>
          </div>
          <CashbackStatusChip status={status} />
        </div>

        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-xs text-muted-foreground">Base rate</p>
            <p className="mt-0.5 text-lg font-semibold text-emerald-400">{rule.flatRatePercent}%</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Earned this month</p>
            <p className="mt-0.5 font-medium">
              {rule.earnedMonth != null ? formatINR(rule.earnedMonth) : formatINR(0)}
            </p>
          </div>
        </div>

        <div className="grid gap-2 text-xs text-muted-foreground">
          {Object.keys(rule.categoryMultipliers).length > 0 ? (
            <p>
              <CreditCard className="mr-1 inline size-3" />
              Category multipliers: {formatMultiplierMap(rule.categoryMultipliers)}
            </p>
          ) : null}
          {Object.keys(rule.merchantMultipliers).length > 0 ? (
            <p>Merchant multipliers: {formatMultiplierMap(rule.merchantMultipliers)}</p>
          ) : null}
          {rule.monthlyCap != null ? (
            <p>
              Monthly cap {formatINR(rule.monthlyCap)}
              {rule.remainingCap != null ? ` · ${formatINR(rule.remainingCap)} left` : null}
            </p>
          ) : null}
          {rule.minimumSpend > 0 ? <p>Minimum spend {formatINR(rule.minimumSpend)}</p> : null}
          {rule.excludedCategoryNames.length > 0 ? (
            <p>Excluded categories: {rule.excludedCategoryNames.join(', ')}</p>
          ) : null}
          {rule.excludedMerchantNames.length > 0 ? (
            <p>Excluded merchants: {rule.excludedMerchantNames.join(', ')}</p>
          ) : null}
        </div>

        <div className="flex items-center justify-between gap-2 pt-1">
          <button
            type="button"
            className="text-xs font-medium text-muted-foreground hover:text-foreground"
            onClick={onSelect}
          >
            View activity
          </button>
          <Link
            to={`/finance/cashback/${rule.id}`}
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
