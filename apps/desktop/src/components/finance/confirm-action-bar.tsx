import { Button } from '@/components/ui/button'

interface ConfirmActionBarProps {
  message: string
  confirmLabel: string
  onConfirm: () => void
  onCancel: () => void
  busy?: boolean
  destructive?: boolean
}

export function ConfirmActionBar({
  message,
  confirmLabel,
  onConfirm,
  onCancel,
  busy = false,
  destructive = false,
}: ConfirmActionBarProps) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-border bg-muted/40 px-3 py-2">
      <p className="text-sm text-muted-foreground">{message}</p>
      <div className="flex items-center gap-2">
        <Button type="button" variant="ghost" size="sm" disabled={busy} onClick={onCancel}>
          Cancel
        </Button>
        <Button
          type="button"
          size="sm"
          variant={destructive ? 'outline' : 'default'}
          className={destructive ? 'border-destructive/50 text-destructive hover:bg-destructive/10' : undefined}
          disabled={busy}
          onClick={onConfirm}
        >
          {confirmLabel}
        </Button>
      </div>
    </div>
  )
}
