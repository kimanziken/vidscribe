export interface Segment {
  id: number
  start: number
  end: number
  text: string
}

export interface Transcript {
  video_id: string
  filename: string
  duration: number
  language: string
  segments: Segment[]
}

export interface Summary {
  video_id: string
  summary: string
}

export interface Job {
  video_id: string
  filename: string
  status: JobStatus
  summarize_requested: boolean
  transcript_path?: string
  summary_path?: string
  chunk_count?: number
  error?: string
}

export type JobStatus =
  | 'uploaded'
  | 'extracting_audio'
  | 'transcribing'
  | 'indexing'
  | 'summarizing'
  | 'done'
  | 'failed'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  streaming?: boolean
}