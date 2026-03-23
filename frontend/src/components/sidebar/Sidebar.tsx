import { useAllJobs } from '@/hooks/useVideos'
import { UploadButton } from './UploadButton'
import { VideoList } from './VideoList'

interface SidebarProps {
  selectedVideoId: string | null
  onSelectVideo: (videoId: string) => void
}

export function Sidebar({ selectedVideoId, onSelectVideo }: SidebarProps) {
  const { data: jobs } = useAllJobs()

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b">
        <h1 className="text-lg font-semibold">Vidscribe</h1>
      </div>
      <UploadButton onUploaded={onSelectVideo} />
      <VideoList
        jobs={jobs ?? []}
        selectedVideoId={selectedVideoId}
        onSelectVideo={onSelectVideo}
      />
    </div>
  )
}