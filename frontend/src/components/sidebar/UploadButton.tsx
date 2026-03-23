import { useRef, useState } from 'react'
import { Button } from '@/components/ui/button'
import { useUploadVideo } from '@/hooks/useVideos'

interface UploadButtonProps {
  onUploaded: (videoId: string) => void
}

export function UploadButton({ onUploaded }: UploadButtonProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [summarize, setSummarize] = useState(false)
  const { mutate: upload, isPending } = useUploadVideo()

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    upload(
      { file, summarize },
      {
        onSuccess: (job) => {
          onUploaded(job.video_id)
          if (inputRef.current) inputRef.current.value = ''
        },
      }
    )
  }

  return (
    <div className="p-4 border-b space-y-3">
      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="summarize"
          checked={summarize}
          onChange={(e) => setSummarize(e.target.checked)}
          className="rounded"
        />
        <label htmlFor="summarize" className="text-sm text-muted-foreground">
          Auto-summarize
        </label>
      </div>
      <Button
        className="w-full"
        disabled={isPending}
        onClick={() => inputRef.current?.click()}
      >
        {isPending ? 'Uploading...' : 'Upload Video'}
      </Button>
      <input
        ref={inputRef}
        type="file"
        accept="video/mp4,video/x-matroska,video/avi,video/quicktime"
        className="hidden"
        onChange={handleFileChange}
      />
    </div>
  )
}