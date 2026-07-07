import { useState } from 'react'
import { Plus } from 'lucide-react'
import { FeedbackBanner } from '@/components/finance/feedback'
import { useFinanceFeedback } from '@/hooks/use-finance-feedback'
import { ScreenHeader } from '@/components/layout/screen-header'
import { TaxonomyRow } from '@/components/finance/taxonomy-row'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { QueryBoundary } from '@/components/query-boundary'
import { useMerchants } from '@/hooks/use-finance'
import { useCreateMerchant, useDeleteMerchant, useUpdateMerchant } from '@/hooks/use-finance-mutations'
import { ApiError } from '@/lib/api-client'

export function FinanceMerchantsScreen() {
  const merchants = useMerchants()
  const createMerchant = useCreateMerchant()
  const updateMerchant = useUpdateMerchant()
  const deleteMerchant = useDeleteMerchant()
  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')
  const { feedback, notify, reset } = useFinanceFeedback()

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault()
    reset()
    try {
      const result = await createMerchant.mutateAsync({ name: name.trim() })
      setName('')
      setShowForm(false)
      notify(result.meta.message)
    } catch (error) {
      notify(error instanceof ApiError ? error.message : 'Could not create merchant.', 'error')
    }
  }

  return (
    <section>
      <ScreenHeader
        title="Merchants"
        description="Manage merchants and vendors referenced on transactions."
        actions={
          <Button size="sm" onClick={() => setShowForm((open) => !open)}>
            <Plus className="h-4 w-4" />
            Add merchant
          </Button>
        }
      />
      <FeedbackBanner feedback={feedback} />
      {showForm ? (
        <Card className="mb-4">
          <CardHeader>
            <CardTitle>Create merchant</CardTitle>
          </CardHeader>
          <CardContent>
            <form className="flex flex-wrap items-end gap-3" onSubmit={handleCreate}>
              <label className="min-w-[14rem] flex-1 space-y-1">
                <span className="text-xs text-muted-foreground">Name</span>
                <input
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                  placeholder="e.g. Amazon, Swiggy"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </label>
              <Button type="submit" size="sm" disabled={createMerchant.isPending}>
                Save
              </Button>
              <Button type="button" variant="ghost" size="sm" onClick={() => setShowForm(false)}>
                Cancel
              </Button>
            </form>
          </CardContent>
        </Card>
      ) : null}
      <QueryBoundary query={merchants} loadingMessage="Loading merchants…">
        {(data) => {
          if (data.length === 0) {
            return (
              <div className="rounded-md border border-dashed border-border p-8 text-center">
                <p className="text-sm font-medium">No Merchants Yet</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Create merchants to track where transactions happen.
                </p>
                <Button className="mt-4" size="sm" onClick={() => setShowForm(true)}>
                  <Plus className="h-4 w-4" />
                  Add merchant
                </Button>
              </div>
            )
          }
          return (
            <div className="grid gap-3">
              {data.map((merchant) => (
                <TaxonomyRow
                  key={merchant.id}
                  id={merchant.id}
                  name={merchant.name}
                  onFeedback={notify}
                  onUpdate={async (merchantId, nextName) => {
                    const result = await updateMerchant.mutateAsync({
                      merchantId,
                      input: { name: nextName },
                    })
                    notify(result.meta.message)
                  }}
                  onDelete={async (merchantId) => {
                    const result = await deleteMerchant.mutateAsync(merchantId)
                    notify(result.meta.message)
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
