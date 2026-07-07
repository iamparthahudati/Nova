import { Link } from 'react-router-dom'
import { Gift } from 'lucide-react'
import { buttonVariants } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export function RewardsEmpty() {
  return (
    <div className="rounded-xl border border-dashed border-border bg-muted/20 p-10 text-center">
      <span className="mx-auto flex size-12 items-center justify-center rounded-full bg-emerald-500/10">
        <Gift className="size-6 text-emerald-400" />
      </span>
      <p className="mt-4 text-base font-medium">No reward programs yet</p>
      <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">
        Create a credit card under Finance → Credit Cards, then configure a reward program for that card.
        Reward events appear here when credit card transactions trigger earn rules.
      </p>
      <Link to="/finance/credit-cards" className={cn(buttonVariants({ size: 'sm' }), 'mt-5 inline-flex')}>
        Go to credit cards
      </Link>
    </div>
  )
}
