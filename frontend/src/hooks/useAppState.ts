import { useState, useCallback } from 'react'

export function useAppState() {
  const [selectedVideoId, setSelectedVideoId] = useState<string | null>(null)
  const [currentTime, setCurrentTime] = useState<number>(0)

  const selectVideo = useCallback((videoId: string) => {
    setSelectedVideoId(videoId)
    setCurrentTime(0)
  }, [])

  return {
    selectedVideoId,
    currentTime,
    setCurrentTime,
    selectVideo,
  }
}