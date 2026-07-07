import { Badge } from '@/components/ui/badge'
import { rewardStatusLabel, rewardStatusTone } from '@/lib/finance/reward-display'
import { cn } from '@/lib/utils'

export function RewardStatusChip({ status }: { status: string }) {
  return (
    <Badge variant="outline" className={cn('font-medium', rewardStatusTone(status))}>
      {rewardStatusLabel(status)}
    </Badge>
  )
}
