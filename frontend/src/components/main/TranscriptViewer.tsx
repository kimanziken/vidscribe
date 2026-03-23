import { useEffect, useRef, useState } from 'react'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { Button } from '@/components/ui/button'
import { ChevronDown, ChevronUp } from 'lucide-react'
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
  const [open, setOpen] = useState(true)
  const { data: transcript, isLoading } = useTranscript(videoId, jobStatus)
  const activeRef = useRef<HTMLButtonElement>(null)

  const activeSegment = transcript?.segments.findIndex(
    (seg) => currentTime >= seg.start && currentTime < seg.end
  ) ?? -1

  useEffect(() => {
    if (activeRef.current) {
      activeRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, [activeSegment])

  return (
    <Collapsible open={open} onOpenChange={setOpen} className="flex flex-col flex-1 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 border-b">
        <h3 className="text-sm font-semibold">
          Transcript
          {transcript && (
            <span className="ml-2 text-xs text-muted-foreground font-normal">
              {transcript.segments.length} segments
            </span>
          )}
        </h3>
        <CollapsibleTrigger asChild>
          <Button variant="ghost" size="sm">
            {open ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </Button>
        </CollapsibleTrigger>
      </div>

      <CollapsibleContent className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center p-8">
            <p className="text-sm text-muted-foreground">Loading transcript...</p>
          </div>
        ) : !transcript ? (
          <div className="flex items-center justify-center p-8">
            <p className="text-sm text-muted-foreground">Transcript not available yet.</p>
          </div>
        ) : (
          <div className="p-4 space-y-1">
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
        )}
      </CollapsibleContent>
    </Collapsible>
  )
}