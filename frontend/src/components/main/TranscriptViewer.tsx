import { useEffect, useRef } from 'react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useTranscript } from '@/hooks/useVideos'
import type { JobStatus, Segment } from '@/types'

interface TranscriptViewerProps {
  videoId: string
  jobStatus?: JobStatus
  currentTime: number
  onSegmentClick: (start: number) => void
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

export function TranscriptViewer({
  videoId,
  jobStatus,
  currentTime,
  onSegmentClick,
}: TranscriptViewerProps) {
  const { data: transcript, isLoading } = useTranscript(videoId, jobStatus)
  const activeRef = useRef<HTMLButtonElement>(null)

  const activeSegment = transcript?.segments.findIndex(
    (seg) => currentTime >= seg.start && currentTime < seg.end
  ) ?? -1

  // Auto scroll to active segment
  useEffect(() => {
    if (activeRef.current) {
      activeRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, [activeSegment])

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-sm text-muted-foreground">Loading transcript...</p>
      </div>
    )
  }

  if (!transcript) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-sm text-muted-foreground">Transcript not available yet.</p>
      </div>
    )
  }

  return (
    <ScrollArea className="flex-1 p-4">
      <div className="space-y-1">
        {transcript.segments.map((seg: Segment, idx: number) => (
          <button
            key={seg.id}
            ref={idx === activeSegment ? activeRef : null}
            onClick={() => onSegmentClick(seg.start)}
            className={`w-full text-left px-3 py-2 rounded-md transition-colors text-sm ${
              idx === activeSegment
                ? 'bg-primary text-primary-foreground'
                : 'hover:bg-accent text-foreground'
            }`}
          >
            <span className="text-xs opacity-60 mr-2 font-mono">
              {formatTime(seg.start)}
            </span>
            {seg.text}
          </button>
        ))}
      </div>
    </ScrollArea>
  )
}