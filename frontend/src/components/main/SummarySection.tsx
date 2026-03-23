import { Button } from '@/components/ui/button'
import { useSummary, useTriggerSummarize, useJobStatus } from '@/hooks/useVideos'
import type { JobStatus } from '@/types'

interface SummarySectionProps {
  videoId: string
  jobStatus?: JobStatus
}

export function SummarySection({ videoId, jobStatus }: SummarySectionProps) {
  const { data: summary, isLoading, refetch } = useSummary(videoId, jobStatus)
  const { mutate: triggerSummarize, isPending } = useTriggerSummarize()
  const { data: job } = useJobStatus(videoId)

  const isSummarizing = job?.status === 'summarizing'

  function handleSummarize() {
    triggerSummarize(videoId, {
      onSuccess: () => {
        setTimeout(() => refetch(), 2000)
      },
    })
  }

  if (isLoading) {
    return (
      <div className="p-4 border-b">
        <p className="text-sm text-muted-foreground">Loading summary...</p>
      </div>
    )
  }

  if (isSummarizing) {
    return (
      <div className="p-4 border-b">
        <p className="text-sm text-muted-foreground animate-pulse">Generating summary...</p>
      </div>
    )
  }

  if (!summary) {
    return (
      <div className="p-4 border-b flex items-center justify-between">
        <p className="text-sm text-muted-foreground">No summary yet.</p>
        <Button
          size="sm"
          variant="outline"
          disabled={isPending}
          onClick={handleSummarize}
        >
          {isPending ? 'Starting...' : 'Generate Summary'}
        </Button>
      </div>
    )
  }

  return (
    <div className="p-4 border-b">
      <h3 className="text-sm font-semibold mb-2">Summary</h3>
      <p className="text-sm text-muted-foreground whitespace-pre-wrap">{summary.summary}</p>
    </div>
  )
}