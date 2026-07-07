import { useState } from 'react'
import { Plus } from 'lucide-react'
import { ScreenHeader } from '@/components/layout/screen-header'
import { TaxonomyRow } from '@/components/finance/taxonomy-row'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { QueryBoundary } from '@/components/query-boundary'
import { useCategories } from '@/hooks/use-finance'
import { useCreateCategory, useDeleteCategory, useUpdateCategory } from '@/hooks/use-finance-mutations'
import { ApiError } from '@/lib/api-client'

export function FinanceCategoriesScreen() {
  const categories = useCategories()
  const createCategory = useCreateCategory()
  const updateCategory = useUpdateCategory()
  const deleteCategory = useDeleteCategory()
  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')
  const [feedback, setFeedback] = useState<string | null>(null)

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault()
    setFeedback(null)
    try {
      const result = await createCategory.mutateAsync({ name: name.trim() })
      setName('')
      setShowForm(false)
      setFeedback(result.meta.message)
    } catch (error) {
      setFeedback(error instanceof ApiError ? error.message : 'Could not create category.')
    }
  }

  return (
    <section>
      <ScreenHeader
        title="Categories"
        description="Manage expense and income categories used on transactions. Categories are shared across transaction types until type metadata is added to the backend."
        actions={
          <Button size="sm" onClick={() => setShowForm((open) => !open)}>
            <Plus className="h-4 w-4" />
            Add category
          </Button>
        }
      />
      {feedback ? <p className="mb-4 text-sm text-emerald-400">{feedback}</p> : null}
      {showForm ? (
        <Card className="mb-4">
          <CardHeader>
            <CardTitle>Create category</CardTitle>
          </CardHeader>
          <CardContent>
            <form className="flex flex-wrap items-end gap-3" onSubmit={handleCreate}>
              <label className="min-w-[14rem] flex-1 space-y-1">
                <span className="text-xs text-muted-foreground">Name</span>
                <input
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                  placeholder="e.g. Groceries, Salary"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </label>
              <Button type="submit" size="sm" disabled={createCategory.isPending}>
                Save
              </Button>
              <Button type="button" variant="ghost" size="sm" onClick={() => setShowForm(false)}>
                Cancel
              </Button>
            </form>
          </CardContent>
        </Card>
      ) : null}
      <QueryBoundary query={categories} loadingMessage="Loading categories…">
        {(data) => {
          if (data.length === 0) {
            return (
              <div className="rounded-md border border-dashed border-border p-8 text-center">
                <p className="text-sm font-medium">No Categories Yet</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Create categories to classify expenses and income on transactions.
                </p>
                <Button className="mt-4" size="sm" onClick={() => setShowForm(true)}>
                  <Plus className="h-4 w-4" />
                  Add category
                </Button>
              </div>
            )
          }
          return (
            <div className="grid gap-3">
              {data.map((category) => (
                <TaxonomyRow
                  key={category.id}
                  id={category.id}
                  name={category.name}
                  onFeedback={setFeedback}
                  onUpdate={async (categoryId, nextName) => {
                    const result = await updateCategory.mutateAsync({
                      categoryId,
                      input: { name: nextName },
                    })
                    setFeedback(result.meta.message)
                  }}
                  onDelete={async (categoryId) => {
                    const result = await deleteCategory.mutateAsync(categoryId)
                    setFeedback(result.meta.message)
                  }}
                />
              ))}
            </div>
          )
        }}
      </QueryBoundary>
    </section>
  )
}
