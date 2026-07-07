import { Link } from 'react-router-dom'
import { Percent } from 'lucide-react'
import { buttonVariants } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export function CashbackEmpty() {
  return (
    <div className="rounded-xl border border-dashed border-border bg-muted/20 p-10 text-center">
      <span className="mx-auto flex size-12 items-center justify-center rounded-full bg-emerald-500/10">
        <Percent className="size-6 text-emerald-400" />
      </span>
      <p className="mt-4 text-base font-medium">No cashback rules yet</p>
      <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">
        Create a credit card, attach a cashback reward program, and define earn rules. Cashback appears here when
        matching credit card transactions are logged.
      </p>
      <div className="mt-5 flex flex-wrap justify-center gap-2">
        <Link to="/finance/credit-cards" className={cn(buttonVariants({ size: 'sm' }))}>
          Go to credit cards
        </Link>
        <Link to="/finance/rewards" className={cn(buttonVariants({ variant: 'outline', size: 'sm' }))}>
          Reward programs
        </Link>
      </div>
    </div>
  )
}
