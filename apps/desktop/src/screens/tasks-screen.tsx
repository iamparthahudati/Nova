import { useState } from 'react'
import { Check, Plus } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ScreenHeader } from '@/components/layout/screen-header'
import { QueryBoundary } from '@/components/query-boundary'
import { useCompleteTask, useCreateTask } from '@/hooks/use-task-mutations'
import { useTasks } from '@/hooks/use-tasks'
import { ApiError } from '@/lib/api-client'

export function TasksScreen() {
  const tasks = useTasks()
  const createTask = useCreateTask()
  const completeTask = useCompleteTask()
  const [showAddForm, setShowAddForm] = useState(false)
  const [text, setText] = useState('')
  const [due, setDue] = useState('')
  const [feedback, setFeedback] = useState<{ tone: 'success' | 'error'; message: string } | null>(null)

  const pending = createTask.isPending || completeTask.isPending

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault()
    setFeedback(null)
    const trimmed = text.trim()
    if (!trimmed) {
      return
    }
    try {
      const result = await createTask.mutateAsync({
        text: trimmed,
        due: due.trim() || undefined,
      })
      setText('')
      setDue('')
      setShowAddForm(false)
      setFeedback({ tone: 'success', message: result.meta?.message ?? 'Task created.' })
    } catch (error) {
      setFeedback({
        tone: 'error',
        message: error instanceof ApiError ? error.message : 'Could not create task.',
      })
    }
  }

  async function handleComplete(taskId: number) {
    setFeedback(null)
    try {
      const result = await completeTask.mutateAsync(taskId)
      setFeedback({ tone: 'success', message: result.meta?.message ?? 'Task marked done.' })
    } catch (error) {
      setFeedback({
        tone: 'error',
        message: error instanceof ApiError ? error.message : 'Could not complete task.',
      })
    }
  }

  return (
    <section>
      <ScreenHeader
        title="Tasks"
        description="Create and complete tasks through the backend API."
        actions={
          <Button
            type="button"
            variant={showAddForm ? 'secondary' : 'default'}
            size="sm"
            disabled={pending}
            onClick={() => setShowAddForm((open) => !open)}
          >
            <Plus className="h-4 w-4" />
            Add task
          </Button>
        }
      />

      {feedback ? (
        <p
          className={`mb-4 text-sm ${feedback.tone === 'success' ? 'text-emerald-400' : 'text-rose-400'}`}
          role="status"
        >
          {feedback.message}
        </p>
      ) : null}

      {showAddForm ? (
        <Card className="mb-4">
          <CardHeader>
            <CardTitle>New task</CardTitle>
          </CardHeader>
          <CardContent>
            <form className="space-y-3" onSubmit={handleCreate}>
              <label className="block space-y-1">
                <span className="text-xs text-muted-foreground">Description</span>
                <input
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                  value={text}
                  onChange={(event) => setText(event.target.value)}
                  placeholder="What needs doing?"
                  disabled={pending}
                  autoFocus
                />
              </label>
              <label className="block space-y-1">
                <span className="text-xs text-muted-foreground">Due date (optional, YYYY-MM-DD)</span>
                <input
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                  type="date"
                  value={due}
                  onChange={(event) => setDue(event.target.value)}
                  disabled={pending}
                />
              </label>
              <div className="flex gap-2">
                <Button type="submit" size="sm" disabled={pending || !text.trim()}>
                  {createTask.isPending ? 'Saving…' : 'Save task'}
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  disabled={pending}
                  onClick={() => setShowAddForm(false)}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Task list</CardTitle>
        </CardHeader>
        <CardContent>
          <QueryBoundary
            query={tasks}
            isEmpty={(data) => data.length === 0}
            loadingMessage="Loading tasks…"
            emptyMessage="No tasks yet."
          >
            {(data) => (
              <div className="space-y-2">
                {data.map((task) => (
                  <div
                    key={task.id}
                    className="flex items-center justify-between gap-3 rounded-md border border-border bg-muted/30 p-3"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium">{task.text}</p>
                      <p className="text-xs text-muted-foreground">
                        created {new Date(task.createdAt).toLocaleDateString()}{' '}
                        {task.due ? `· due ${task.due}` : ''}
                      </p>
                    </div>
                    <div className="flex shrink-0 items-center gap-2">
                      {task.status === 'open' ? (
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          disabled={pending}
                          onClick={() => void handleComplete(task.id)}
                        >
                          <Check className="h-4 w-4" />
                          {completeTask.isPending && completeTask.variables === task.id ? 'Done…' : 'Done'}
                        </Button>
                      ) : null}
                      <Badge variant={task.status === 'open' ? 'default' : 'secondary'}>{task.status}</Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </QueryBoundary>
        </CardContent>
      </Card>
    </section>
  )
}
