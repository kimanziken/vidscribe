import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getStatus,
  getTranscript,
  getSummary,
  uploadVideo,
  triggerSummarize,
  triggerIndex,
  getAllJobs,
} from '@/api/client'
import type { JobStatus } from '@/types'

const ACTIVE_STATUSES: JobStatus[] = [
  'uploaded',
  'extracting_audio',
  'transcribing',
  'indexing',
  'summarizing',
]

export function useAllJobs() {
  return useQuery({
    queryKey: ['jobs'],
    queryFn: getAllJobs,
  })
}

// Poll a single job status
export function useJobStatus(videoId: string | null) {
  return useQuery({
    queryKey: ['job', videoId],
    queryFn: () => getStatus(videoId!),
    enabled: !!videoId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status && ACTIVE_STATUSES.includes(status) ? 3000 : false
    },
  })
}

// Fetch transcript — only when job is done
export function useTranscript(videoId: string | null, jobStatus?: JobStatus) {
  return useQuery({
    queryKey: ['transcript', videoId],
    queryFn: () => getTranscript(videoId!),
    enabled: !!videoId && jobStatus === 'done',
  })
}

// Fetch summary — only when job is done
export function useSummary(videoId: string | null, jobStatus?: JobStatus) {
  return useQuery({
    queryKey: ['summary', videoId],
    queryFn: () => getSummary(videoId!),
    enabled: !!videoId && jobStatus === 'done',
    retry: false, // don't retry if summary doesn't exist yet
  })
}

// Upload video
export function useUploadVideo() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ file, summarize }: { file: File; summarize: boolean }) =>
      uploadVideo(file, summarize),
    onSuccess: (data) => {
      queryClient.setQueryData(['job', data.video_id], data)
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
    },
  })
}

// Trigger summarization
export function useTriggerSummarize() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (videoId: string) => triggerSummarize(videoId),
    onSuccess: (_, videoId) => {
      queryClient.invalidateQueries({ queryKey: ['job', videoId] })
    },
  })
}

// Trigger indexing
export function useTriggerIndex() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (videoId: string) => triggerIndex(videoId),
    onSuccess: (_, videoId) => {
      queryClient.invalidateQueries({ queryKey: ['job', videoId] })
    },
  })
}