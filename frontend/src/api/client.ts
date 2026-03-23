import type { Job, Transcript, Summary } from '@/types'

const BASE = '/api/v1'

export async function getAllJobs(): Promise<Job[]> {
  const res = await fetch(`${BASE}/jobs`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function uploadVideo(
  file: File,
  summarize: boolean = false
): Promise<Job> {
  const formData = new FormData()
  formData.append('file', file)
  const res = await fetch(`${BASE}/upload?summarize=${summarize}`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getStatus(videoId: string): Promise<Job> {
  const res = await fetch(`${BASE}/status/${videoId}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getTranscript(videoId: string): Promise<Transcript> {
  const res = await fetch(`${BASE}/transcript/${videoId}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getSummary(videoId: string): Promise<Summary> {
  const res = await fetch(`${BASE}/summary/${videoId}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function triggerSummarize(videoId: string): Promise<void> {
  const res = await fetch(`${BASE}/summarize/${videoId}`, { method: 'POST' })
  if (!res.ok) throw new Error(await res.text())
}

export async function triggerIndex(videoId: string): Promise<void> {
  const res = await fetch(`${BASE}/index/${videoId}`, { method: 'POST' })
  if (!res.ok) throw new Error(await res.text())
}

export async function streamChat(
  videoId: string,
  question: string,
  onToken: (token: string) => void,
  onDone: () => void
): Promise<void> {
  const res = await fetch(`${BASE}/chat/${videoId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  })

  if (!res.ok) throw new Error(await res.text())

  const reader = res.body!.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    const token = decoder.decode(value)
    onToken(token)
  }

  onDone()
}