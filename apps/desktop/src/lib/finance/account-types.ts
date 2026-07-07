import type { LucideIcon } from 'lucide-react'
import {
  Banknote,
  CircleDot,
  CreditCard,
  Landmark,
  PiggyBank,
  TrendingUp,
  Wallet,
} from 'lucide-react'

/** Display labels for finance account types. Backend enum is the source of truth. */
export const ACCOUNT_TYPE_LABELS: Record<string, string> = {
  cash: 'Cash',
  bank: 'Bank',
  wallet: 'Wallet',
  credit_card: 'Credit Card',
  loan: 'Loan',
  investment: 'Investment',
  other: 'Other',
  savings: 'Savings Account',
  upi: 'UPI Balance',
  fixed_deposit: 'Fixed Deposit',
  recurring_deposit: 'Recurring Deposit',
  crypto: 'Crypto Wallet',
  digital_gold: 'Digital Gold',
  other_asset: 'Other Asset',
  other_liability: 'Other Liability',
}

export const REGISTRY_ACCOUNT_TYPES = [
  { value: 'cash', label: 'Cash', icon: Banknote },
  { value: 'bank', label: 'Bank', icon: Landmark },
  { value: 'wallet', label: 'Wallet', icon: Wallet },
  { value: 'credit_card', label: 'Credit Card', icon: CreditCard },
  { value: 'investment', label: 'Investment', icon: TrendingUp },
  { value: 'loan', label: 'Loan', icon: PiggyBank },
  { value: 'other', label: 'Other', icon: CircleDot },
] as const satisfies ReadonlyArray<{ value: string; label: string; icon: LucideIcon }>

/** Account types users can create from the Accounts screen (credit cards use their own screen). */
export const CREATABLE_ACCOUNT_TYPES = REGISTRY_ACCOUNT_TYPES.filter(
  (entry) => entry.value !== 'credit_card',
)

export function accountTypeLabel(type: string): string {
  return ACCOUNT_TYPE_LABELS[type] ?? type.replace(/_/g, ' ')
}

export function accountTypeIcon(type: string): LucideIcon {
  return REGISTRY_ACCOUNT_TYPES.find((entry) => entry.value === type)?.icon ?? CircleDot
}

export function isAssetAccount(type: string, classification?: string): boolean {
  if (classification) return classification === 'asset'
  return type !== 'credit_card' && type !== 'loan'
}

export function isTransferEligible(account: { type: string; classification: string; archivedAt?: string | null }): boolean {
  return isAssetAccount(account.type, account.classification) && !account.archivedAt
}
