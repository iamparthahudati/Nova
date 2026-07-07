import { Badge } from '@/components/ui/badge'
import { cashbackStatusLabel, cashbackStatusTone } from '@/lib/finance/cashback-display'
import { cn } from '@/lib/utils'

export function CashbackStatusChip({ status }: { status: string }) {
  return (
    <Badge variant="outline" className={cn('font-medium', cashbackStatusTone(status))}>
      {cashbackStatusLabel(status)}
    </Badge>
  )
}
