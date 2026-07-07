import type { FinanceCreditCard, FinanceStatement } from '@/view-models/finance'

const KNOWN_BANKS = [
  'HDFC',
  'ICICI',
  'SBI',
  'Axis',
  'Kotak',
  'Amex',
  'American Express',
  'Citibank',
  'Citi',
  'IndusInd',
  'Yes Bank',
  'RBL',
  'IDFC',
  'Federal',
  'BOB',
  'PNB',
  'Union Bank',
  'Canara',
  'HSBC',
  'Standard Chartered',
  'AU Bank',
  'DBS',
]

export function deriveBankName(cardName: string): string {
  const trimmed = cardName.trim()
  if (!trimmed) return 'Credit card'
  const upper = trimmed.toUpperCase()
  for (const bank of KNOWN_BANKS) {
    if (upper.startsWith(bank.toUpperCase())) return bank
    if (upper.includes(` ${bank.toUpperCase()} `)) return bank
  }
  const firstWord = trimmed.split(/\s+/)[0]
  return firstWord.length >= 2 ? firstWord : 'Credit card'
}

export function displayCardName(card: Pick<FinanceCreditCard, 'name'>): string {
  return cardProductName(card.name)
}

export function cardProductName(name: string): string {
  const bank = deriveBankName(name)
  if (name.toLowerCase().startsWith(bank.toLowerCase())) {
    const rest = name.slice(bank.length).trim()
    return rest || name
  }
  return name
}

export function networkLabel(network?: string | null): string | null {
  if (!network?.trim()) return null
  const normalized = network.trim().toLowerCase()
  if (normalized.includes('visa')) return 'Visa'
  if (normalized.includes('master')) return 'Mastercard'
  if (normalized.includes('rupay')) return 'RuPay'
  if (normalized.includes('amex') || normalized.includes('american')) return 'Amex'
  return network.trim()
}

export function networkAccentClass(network?: string | null): string {
  const label = networkLabel(network)?.toLowerCase() ?? ''
  if (label.includes('visa')) return 'from-blue-700 via-blue-600 to-indigo-700'
  if (label.includes('master')) return 'from-orange-700 via-red-600 to-rose-700'
  if (label.includes('rupay')) return 'from-emerald-700 via-teal-600 to-cyan-700'
  if (label.includes('amex')) return 'from-slate-700 via-zinc-600 to-neutral-700'
  return 'from-violet-800 via-purple-700 to-fuchsia-800'
}

export type StatusTone = 'default' | 'positive' | 'negative' | 'warning'

export function statementStatusTone(status?: string | null): StatusTone {
  const value = status?.toLowerCase() ?? ''
  if (value === 'paid') return 'positive'
  if (value === 'overdue') return 'negative'
  if (value === 'partial' || value === 'generated' || value === 'open') return 'warning'
  return 'default'
}

export function statementStatusClass(tone: StatusTone): string {
  if (tone === 'positive') return 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400'
  if (tone === 'negative') return 'border-rose-500/40 bg-rose-500/10 text-rose-400'
  if (tone === 'warning') return 'border-amber-500/40 bg-amber-500/10 text-amber-400'
  return 'border-border bg-muted/30 text-muted-foreground'
}

export function utilizationTone(percent: number): StatusTone {
  if (percent >= 80) return 'negative'
  if (percent >= 50) return 'warning'
  return 'positive'
}

export function formatBillingSchedule(statementDay: number, dueDayOffset: number): string {
  return `Bills on day ${statementDay} · due in ${dueDayOffset} days`
}

export function formatDueDay(statementDay: number, dueDayOffset: number): string {
  const dueDay = Math.min(statementDay + dueDayOffset, 28)
  return `Day ${dueDay}`
}

export function statementUtilizationPercent(statement: FinanceStatement, creditLimit: number): number {
  if (!creditLimit || creditLimit <= 0) return 0
  const spend = statement.spend ?? 0
  return Math.min(Math.max((spend / creditLimit) * 100, 0), 100)
}
