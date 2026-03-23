import { useState } from 'react'
import { VideoPlayer } from './VideoPlayer'
import { SummarySection } from './SummarySection'
import { TranscriptViewer } from './TranscriptViewer'
import { useJobStatus } from '@/hooks/useVideos'

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

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <VideoPlayer
        videoId={videoId}
        onTimeUpdate={onTimeUpdate}
        seekTo={seekTo}
      />
      <div className="flex flex-col flex-1 overflow-hidden">
        <SummarySection
          videoId={videoId}
          jobStatus={job?.status}
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