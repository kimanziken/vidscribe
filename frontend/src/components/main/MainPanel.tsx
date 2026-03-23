import { useState } from 'react'
import { VideoPlayer } from './VideoPlayer'
import { SummarySection } from './SummarySection'
import { TranscriptViewer } from './TranscriptViewer'
import { useJobStatus } from '@/hooks/useVideos'
import type { JobStatus } from '@/types'

const ACTIVE_STATUSES: JobStatus[] = [
  'uploaded',
  'extracting_audio',
  'transcribing',
  'indexing',
  'summarizing',
]

const STATUS_LABELS: Record<JobStatus, string> = {
  uploaded: 'Uploaded — waiting to process...',
  extracting_audio: 'Extracting audio...',
  transcribing: 'Transcribing video — this may take a while...',
  indexing: 'Indexing transcript for chat...',
  summarizing: 'Generating summary...',
  done: '',
  failed: 'Processing failed.',
}

interface MainPanelProps {
  videoId: string | null
  currentTime: number
  onTimeUpdate: (time: number) => void
}

export function MainPanel({ videoId, currentTime, onTimeUpdate }: MainPanelProps) {
  const [seekTo, setSeekTo] = useState<number | undefined>()
  const { data: job } = useJobStatus(videoId)

  if (!videoId) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-muted-foreground text-sm">Select a video to get started.</p>
      </div>
    )
  }

  const isProcessing = job?.status && ACTIVE_STATUSES.includes(job.status)
  const isFailed = job?.status === 'failed'

  return (
    <div className="flex flex-col h-full overflow-hidden">

      {/* Processing indicator */}
      {isProcessing && (
        <div className="flex items-center gap-3 px-4 py-2 bg-muted border-b">
          <div className="w-3 h-3 rounded-full bg-primary animate-pulse shrink-0" />
          <p className="text-sm text-muted-foreground">
            {STATUS_LABELS[job!.status]}
          </p>
        </div>
      )}

      {/* Failed indicator */}
      {isFailed && (
        <div className="flex items-center gap-3 px-4 py-2 bg-destructive/10 border-b">
          <p className="text-sm text-destructive">
            {job?.error ?? 'An error occurred during processing.'}
          </p>
        </div>
      )}

      {/* Video player — show as soon as video is uploaded */}
      {job && job.status !== 'failed' && (
        <VideoPlayer
          videoId={videoId}
          onTimeUpdate={onTimeUpdate}
          seekTo={seekTo}
        />
      )}

      <div className="flex flex-col flex-1 overflow-hidden">
        <SummarySection
          videoId={videoId}
          jobStatus={job?.status}
          isProcessing={!!isProcessing}
        />
        <TranscriptViewer
          videoId={videoId}
          jobStatus={job?.status}
          currentTime={currentTime}
          onSegmentClick={(start) => setSeekTo(start)}
        />
      </div>
    </div>
  )
}