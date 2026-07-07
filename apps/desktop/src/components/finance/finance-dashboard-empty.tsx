import { Link } from 'react-router-dom'
import { Banknote, CreditCard, PlusCircle, Receipt, Wallet } from 'lucide-react'
import { buttonVariants } from '@/components/ui/button'
import { cn } from '@/lib/utils'

const steps = [
  {
    icon: Banknote,
    title: 'Add your accounts',
    description: 'Cash, bank, and wallet balances power net worth and cash available.',
    to: '/finance/accounts',
    label: 'Add account',
  },
  {
    icon: CreditCard,
    title: 'Set up credit cards',
    description: 'Track limits, utilization, and statement due dates in one place.',
    to: '/finance/credit-cards',
    label: 'Add credit card',
  },
  {
    icon: Receipt,
    title: 'Log transactions',
    description: 'Income and expenses feed your monthly snapshot and recent activity.',
    to: '/finance/transactions',
    label: 'Add transaction',
  },
]

export function FinanceDashboardEmpty() {
  return (
    <div className="rounded-2xl border border-dashed border-border bg-muted/10 p-8 text-center sm:p-12">
      <div className="mx-auto flex size-16 items-center justify-center rounded-full border border-emerald-500/30 bg-emerald-500/10">
        <Wallet className="size-8 text-emerald-400" />
      </div>
      <h2 className="mt-5 text-xl font-semibold">Your financial command center</h2>
      <p className="mx-auto mt-2 max-w-lg text-sm text-muted-foreground">
        Add accounts, cards, and transactions to unlock net worth, utilization, monthly cash flow, and
        upcoming payment alerts — all projected from your backend ledger.
      </p>
      <div className="mt-8 grid gap-4 text-left sm:grid-cols-3">
        {steps.map(({ icon: Icon, title, description, to, label }) => (
          <div
            key={to}
            className="rounded-xl border border-border/70 bg-background/60 p-4 transition-colors hover:border-emerald-500/30"
          >
            <div className="flex size-10 items-center justify-center rounded-lg bg-muted/50">
              <Icon className="size-5 text-emerald-400" />
            </div>
            <p className="mt-3 text-sm font-medium">{title}</p>
            <p className="mt-1 text-xs text-muted-foreground">{description}</p>
            <Link to={to} className={cn(buttonVariants({ variant: 'outline', size: 'sm' }), 'mt-4 inline-flex')}>
              <PlusCircle className="size-4" />
              {label}
            </Link>
          </div>
        ))}
      </div>
    </div>
  )
}
