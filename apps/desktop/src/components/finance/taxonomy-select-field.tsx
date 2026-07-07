import { useState } from 'react'
import { Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ApiError } from '@/lib/api-client'

interface TaxonomyOption {
  id: number
  name: string
}

interface TaxonomySelectFieldProps {
  label: string
  placeholder: string
  emptyLabel: string
  addLabel: string
  value: number | ''
  options: TaxonomyOption[]
  onChange: (value: number | '') => void
  onCreate: (name: string) => Promise<{ id: number }>
  required?: boolean
}

export function TaxonomySelectField({
  label,
  placeholder,
  emptyLabel,
  addLabel,
  value,
  options,
  onChange,
  onCreate,
  required = false,
}: TaxonomySelectFieldProps) {
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault()
    const trimmed = name.trim()
    if (!trimmed) return
    setError(null)
    setCreating(true)
    try {
      const created = await onCreate(trimmed)
      onChange(created.id)
      setName('')
      setShowCreate(false)
    } catch (createError) {
      setError(createError instanceof ApiError ? createError.message : `Could not create ${label.toLowerCase()}.`)
    } finally {
      setCreating(false)
    }
  }

  if (options.length === 0 && !showCreate) {
    return (
      <div className="space-y-2 rounded-md border border-dashed border-border p-3">
        <p className="text-sm font-medium">{emptyLabel}</p>
        <p className="text-xs text-muted-foreground">Create one to use it on this transaction.</p>
        <Button type="button" size="sm" variant="outline" onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4" />
          {addLabel}
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <label className="space-y-1">
        <span className="text-xs text-muted-foreground">{label}</span>
        <select
          className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
          value={value}
          onChange={(e) => onChange(e.target.value ? Number(e.target.value) : '')}
          required={required}
        >
          <option value="">{placeholder}</option>
          {options.map((option) => (
            <option key={option.id} value={option.id}>
              {option.name}
            </option>
          ))}
        </select>
      </label>
      {showCreate ? (
        <form className="flex flex-wrap items-end gap-2" onSubmit={handleCreate}>
          <input
            className="min-w-[10rem] flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm"
            placeholder={`${label} name`}
            value={name}
            onChange={(e) => setName(e.target.value)}
            autoFocus
            required
          />
          <Button type="submit" size="sm" disabled={creating}>
            Save
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => {
              setShowCreate(false)
              setName('')
              setError(null)
            }}
          >
            Cancel
          </Button>
        </form>
      ) : (
        <Button type="button" variant="outline" size="sm" onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4" />
          {addLabel}
        </Button>
      )}
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
    </div>
  )
}
