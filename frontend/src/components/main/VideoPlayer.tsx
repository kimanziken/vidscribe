import { useRef, useEffect } from 'react'

interface VideoPlayerProps {
  videoId: string
  onTimeUpdate: (time: number) => void
  seekTo?: number
}

export function VideoPlayer({ videoId, onTimeUpdate, seekTo }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)

  // Seek when seekTo changes
  useEffect(() => {
    if (videoRef.current && seekTo !== undefined) {
      videoRef.current.currentTime = seekTo
      videoRef.current.play()
    }
  }, [seekTo])

  return (
    <div className="w-full bg-black">
      <video
        ref={videoRef}
        className="w-full max-h-64 object-contain"
        controls
        onTimeUpdate={() => {
          if (videoRef.current) {
            onTimeUpdate(videoRef.current.currentTime)
          }
        }}
        src={`/api/v1/video/${videoId}`}
      />
    </div>
  )
}