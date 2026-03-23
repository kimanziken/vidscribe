import { useState } from 'react'
import { Button } from '@/components/ui/button'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { useSummary, useTriggerSummarize, useJobStatus } from '@/hooks/useVideos'
import type { JobStatus } from '@/types'

interface SummarySectionProps {
  videoId: string
  jobStatus?: JobStatus
  isProcessing: boolean
}

export function SummarySection({ videoId, jobStatus, isProcessing }: SummarySectionProps) {
  const [open, setOpen] = useState(false)
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

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <div className="flex items-center justify-between px-4 py-2 border-b">
        <h3 className="text-sm font-semibold">Summary</h3>
        <div className="flex items-center gap-2">
          {!summary && !isSummarizing && !isLoading && !isProcessing && (
            <Button
              size="sm"
              variant="outline"
              disabled={isPending}
              onClick={handleSummarize}
            >
              {isPending ? 'Starting...' : 'Generate'}
            </Button>
          )}
          {isSummarizing && (
            <span className="text-xs text-muted-foreground animate-pulse">
              Generating...
            </span>
          )}
          {isProcessing && (
            <span className="text-xs text-muted-foreground">
              Available after processing
            </span>
          )}
          {summary && (
            <CollapsibleTrigger asChild>
              <Button variant="ghost" size="sm">
                {open ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </Button>
            </CollapsibleTrigger>
          )}
        </div>
      </div>
      <CollapsibleContent>
        <div className="px-4 py-3 border-b max-h-48 overflow-y-auto">
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : summary ? (
            <p className="text-sm text-muted-foreground whitespace-pre-wrap">
              {summary.summary}
            </p>
          ) : null}
        </div>
      </CollapsibleContent>
    </Collapsible>
  )
}