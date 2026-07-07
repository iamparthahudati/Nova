import { Search, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { TRANSACTION_KINDS } from '@/lib/finance/transaction-kinds'
import type { FinanceAccount, FinanceCategory, FinanceMerchant } from '@/view-models/finance'

export interface TransactionFilterState {
  accountId?: number
  categoryId?: number
  merchantId?: number
  kind: string
  startDate: string
  endDate: string
  search: string
}

interface TransactionFiltersProps {
  filters: TransactionFilterState
  accounts: FinanceAccount[]
  categories: FinanceCategory[]
  merchants: FinanceMerchant[]
  onChange: (next: TransactionFilterState) => void
  onReset: () => void
}

const selectClass =
  'rounded-md border border-border bg-background px-3 py-2 text-sm'

export function TransactionFilters({
  filters,
  accounts,
  categories,
  merchants,
  onChange,
  onReset,
}: TransactionFiltersProps) {
  const hasActiveFilters = Boolean(
    filters.accountId ||
      filters.categoryId ||
      filters.merchantId ||
      filters.kind ||
      filters.startDate ||
      filters.endDate ||
      filters.search,
  )

  function patch(partial: Partial<TransactionFilterState>) {
    onChange({ ...filters, ...partial })
  }

  return (
    <div className="space-y-3 rounded-lg border border-border bg-muted/20 p-3">
      <div className="flex flex-wrap gap-2">
        <select
          className={selectClass}
          value={filters.accountId ?? ''}
          onChange={(e) => patch({ accountId: e.target.value ? Number(e.target.value) : undefined })}
        >
          <option value="">All accounts</option>
          {accounts.map((account) => (
            <option key={account.id} value={account.id}>
              {account.name}
            </option>
          ))}
        </select>
        <select
          className={selectClass}
          value={filters.kind}
          onChange={(e) => patch({ kind: e.target.value })}
        >
          <option value="">All types</option>
          {TRANSACTION_KINDS.map((kind) => (
            <option key={kind.value} value={kind.value}>
              {kind.label}
            </option>
          ))}
        </select>
        <select
          className={selectClass}
          value={filters.categoryId ?? ''}
          onChange={(e) => patch({ categoryId: e.target.value ? Number(e.target.value) : undefined })}
        >
          <option value="">All categories</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>
        <select
          className={selectClass}
          value={filters.merchantId ?? ''}
          onChange={(e) => patch({ merchantId: e.target.value ? Number(e.target.value) : undefined })}
        >
          <option value="">All merchants</option>
          {merchants.map((merchant) => (
            <option key={merchant.id} value={merchant.id}>
              {merchant.name}
            </option>
          ))}
        </select>
      </div>
      <div className="flex flex-wrap gap-2">
        <label className="space-y-1">
          <span className="text-xs text-muted-foreground">From</span>
          <input
            type="date"
            className={selectClass}
            value={filters.startDate}
            onChange={(e) => patch({ startDate: e.target.value })}
          />
        </label>
        <label className="space-y-1">
          <span className="text-xs text-muted-foreground">To</span>
          <input
            type="date"
            className={selectClass}
            value={filters.endDate}
            onChange={(e) => patch({ endDate: e.target.value })}
          />
        </label>
        <label className="min-w-[12rem] flex-1 space-y-1">
          <span className="text-xs text-muted-foreground">Search</span>
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <input
              className="w-full rounded-md border border-border bg-background py-2 pl-9 pr-3 text-sm"
              placeholder="Notes, merchants, categories…"
              value={filters.search}
              onChange={(e) => patch({ search: e.target.value })}
            />
          </div>
        </label>
        {hasActiveFilters ? (
          <div className="flex items-end">
            <Button type="button" variant="ghost" size="sm" onClick={onReset}>
              <X className="size-4" />
              Clear filters
            </Button>
          </div>
        ) : null}
      </div>
    </div>
  )
}
