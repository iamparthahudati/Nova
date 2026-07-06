import { ScreenHeader } from '@/components/layout/screen-header'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { QueryBoundary } from '@/components/query-boundary'
import { useSettings } from '@/hooks/use-settings'
import { useAppStore } from '@/store/app-store'

export function SettingsScreen() {
  const settings = useSettings()
  const { theme, setTheme } = useAppStore()

  return (
    <section>
      <ScreenHeader title="Settings" description="Assistant configuration and profile observations from the backend." />
      <QueryBoundary query={settings} loadingMessage="Loading settings…">
        {(data) => (
          <div className="grid gap-4 xl:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Appearance</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <p className="text-muted-foreground">Current theme: {theme}</p>
                <div className="flex gap-2">
                  <Button variant="secondary" onClick={() => setTheme('light')}>
                    Light
                  </Button>
                  <Button variant="secondary" onClick={() => setTheme('dark')}>
                    Dark
                  </Button>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Assistant configuration</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p>
                  <span className="text-muted-foreground">Assistant:</span> {data.assistantName}
                </p>
                <p>
                  <span className="text-muted-foreground">Voice:</span> {data.voiceName}
                </p>
                <p>
                  <span className="text-muted-foreground">Briefing:</span> {data.briefingTime}
                </p>
                <p>
                  <span className="text-muted-foreground">Model:</span> {data.claudeModel}
                </p>
                <div className="flex flex-wrap gap-2 pt-1">
                  <Badge variant={data.semanticMemoryEnabled ? 'default' : 'secondary'}>Semantic memory</Badge>
                  <Badge variant={data.entityExtractionEnabled ? 'default' : 'secondary'}>Entity extraction</Badge>
                  <Badge variant={data.graphContextEnabled ? 'default' : 'secondary'}>Graph context</Badge>
                </div>
              </CardContent>
            </Card>
            <Card className="xl:col-span-2">
              <CardHeader>
                <CardTitle>Profile observations</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                {data.observations.length === 0 ? (
                  <p className="text-muted-foreground">No profile observations yet.</p>
                ) : (
                  data.observations.map((observation) => (
                    <div key={observation.id} className="rounded-md border border-border bg-muted/30 p-3">
                      <div className="mb-1 flex items-center gap-2">
                        <Badge variant="outline">{observation.category}</Badge>
                        <span className="text-xs text-muted-foreground">confidence {observation.confidence.toFixed(2)}</span>
                      </div>
                      <p>{observation.observation}</p>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </QueryBoundary>
    </section>
  )
}
