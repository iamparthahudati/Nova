import { useState } from 'react'
import { Pencil, Trash2 } from 'lucide-react'
import { ConfirmActionBar } from '@/components/finance/confirm-action-bar'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { ApiError } from '@/lib/api-client'

interface TaxonomyRowProps {
  id: number
  name: string
  onUpdate: (id: number, name: string) => Promise<void>
  onDelete: (id: number) => Promise<void>
  onFeedback: (message: string) => void
  deleteLabel?: string
}

export function TaxonomyRow({
  id,
  name,
  onUpdate,
  onDelete,
  onFeedback,
  deleteLabel = 'Delete',
}: TaxonomyRowProps) {
  const [editing, setEditing] = useState(false)
  const [pendingDelete, setPendingDelete] = useState(false)
  const [draft, setDraft] = useState(name)
  const [busy, setBusy] = useState(false)

  async function handleUpdate(event: React.FormEvent) {
    event.preventDefault()
    const trimmed = draft.trim()
    if (!trimmed || trimmed === name) {
      setEditing(false)
      setDraft(name)
      return
    }
    setBusy(true)
    try {
      await onUpdate(id, trimmed)
      setEditing(false)
    } catch (error) {
      onFeedback(error instanceof ApiError ? error.message : 'Could not update.')
    } finally {
      setBusy(false)
    }
  }

  async function handleDelete() {
    setBusy(true)
    try {
      await onDelete(id)
      setPendingDelete(false)
    } catch (error) {
      onFeedback(error instanceof ApiError ? error.message : 'Could not delete.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card>
      <CardContent className="space-y-3 p-4">
        {pendingDelete ? (
          <ConfirmActionBar
            message={`Delete "${name}"? This removes it from active lists.`}
            confirmLabel={deleteLabel}
            destructive
            busy={busy}
            onCancel={() => setPendingDelete(false)}
            onConfirm={() => void handleDelete()}
          />
        ) : null}
        <div className="flex items-center justify-between gap-3">
        {editing ? (
          <form className="flex flex-1 flex-wrap items-center gap-2" onSubmit={handleUpdate}>
            <input
              className="min-w-[12rem] flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              autoFocus
              required
            />
            <Button type="submit" size="sm" disabled={busy}>
              Save
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              disabled={busy}
              onClick={() => {
                setEditing(false)
                setDraft(name)
              }}
            >
              Cancel
            </Button>
          </form>
        ) : (
          <>
            <p className="font-medium">{name}</p>
            <div className="flex items-center gap-1">
              <Button variant="ghost" size="icon" className="size-8" disabled={busy} onClick={() => setEditing(true)}>
                <Pencil className="size-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="size-8 text-muted-foreground hover:text-destructive"
                disabled={busy}
                onClick={() => setPendingDelete(true)}
              >
                <Trash2 className="size-4" />
                <span className="sr-only">{deleteLabel}</span>
              </Button>
            </div>
          </>
        )}
        </div>
      </CardContent>
    </Card>
  )
}
