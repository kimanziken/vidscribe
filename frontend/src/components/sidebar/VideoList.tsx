import { useJobStatus } from '@/hooks/useVideos'
import { StatusBadge } from '@/components/StatusBadge'
import type { Job } from '@/types'

interface VideoItemProps {
  job: Job
  isSelected: boolean
  onSelect: (videoId: string) => void
}

function VideoItem({ job, isSelected, onSelect }: VideoItemProps) {
  const { data: liveJob } = useJobStatus(job.video_id)
  const currentJob = liveJob ?? job

  return (
    <button
      onClick={() => onSelect(currentJob.video_id)}
      className={`w-full text-left px-4 py-3 border-b hover:bg-accent transition-colors ${
        isSelected ? 'bg-accent' : ''
      }`}
    >
      <p className="text-sm font-medium truncate">{currentJob.filename}</p>
      <div className="mt-1">
        <StatusBadge status={currentJob.status} />
      </div>
    </button>
  )
}

interface VideoListProps {
  jobs: Job[]
  selectedVideoId: string | null
  onSelectVideo: (videoId: string) => void
}

export function VideoList({ jobs, selectedVideoId, onSelectVideo }: VideoListProps) {
  if (jobs.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-4">
        <p className="text-sm text-muted-foreground text-center">
          No videos yet. Upload one to get started.
        </p>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto">
      {jobs.map((job) => (
        <VideoItem
          key={job.video_id}
          job={job}
          isSelected={selectedVideoId === job.video_id}
          onSelect={onSelectVideo}
        />
      ))}
    </div>
  )
}