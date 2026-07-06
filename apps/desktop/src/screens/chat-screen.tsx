import { ScreenHeader } from '@/components/layout/screen-header'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export function ChatScreen() {
  return (
    <section>
      <ScreenHeader
        title="Chat"
        description="Conversation workspace. Backend integration is deferred until conversation history is available."
      />
      <Card>
        <CardHeader>
          <CardTitle>Chat unavailable</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Chat backend integration will be implemented after conversation history becomes available.
          </p>
        </CardContent>
      </Card>
    </section>
  )
}
