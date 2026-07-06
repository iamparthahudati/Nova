import type { SpendingResponse, SpendingTransactionResponse } from '@nova/api-contracts'
import type { SpendingEntry, SpendingViewModel } from '@/view-models'

export function mapSpendingTransaction(row: SpendingTransactionResponse): SpendingEntry {
  return {
    id: row.id,
    type: row.type,
    amount: row.amount,
    note: row.note ?? undefined,
    createdAt: row.created_at,
  }
}

export function mapSpending(response: SpendingResponse): SpendingViewModel {
  return {
    earnedMonth: response.earned_month,
    spentMonth: response.spent_month,
    transactions: response.transactions.map(mapSpendingTransaction),
  }
}
