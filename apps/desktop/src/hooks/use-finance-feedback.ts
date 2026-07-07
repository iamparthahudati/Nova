import { useCallback, useState } from 'react'

export type FeedbackTone = 'success' | 'error'

export interface FinanceFeedback {
  message: string
  tone: FeedbackTone
}

/**
 * Shared feedback state for finance screens. `notify` defaults to a success
 * tone so success paths stay terse; error paths pass `'error'` explicitly.
 */
export function useFinanceFeedback() {
  const [feedback, setFeedback] = useState<FinanceFeedback | null>(null)
  const notify = useCallback(
    (message: string, tone: FeedbackTone = 'success') => setFeedback({ message, tone }),
    [],
  )
  const reset = useCallback(() => setFeedback(null), [])
  return { feedback, notify, reset }
}
