import { useEffect, useRef } from 'react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { ChatInput } from './ChatInput'
import { useStream } from '@/hooks/useStream'
import { useJobStatus } from '@/hooks/useVideos'
import type { ChatMessage } from '@/types'

interface MessageBubbleProps {
  message: ChatMessage
}

function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
      <div
        className={`max-w-[85%] rounded-lg px-4 py-2 text-sm ${
          isUser
            ? 'bg-primary text-primary-foreground'
            : 'bg-muted text-foreground'
        }`}
      >
        <p className="whitespace-pre-wrap">
          {message.content}
          {message.streaming && (
            <span className="inline-block w-1.5 h-3.5 bg-current ml-0.5 animate-pulse" />
          )}
        </p>
      </div>
    </div>
  )
}

interface ChatPanelProps {
  videoId: string | null
}

export function ChatPanel({ videoId }: ChatPanelProps) {
  const { messages, isStreaming, sendMessage, clearMessages } = useStream()
  const { data: job } = useJobStatus(videoId)
  const bottomRef = useRef<HTMLDivElement>(null)

  const isReady = job?.status === 'done' && !!job?.chunk_count

  // Clear messages when video changes
  useEffect(() => {
    clearMessages()
  }, [videoId, clearMessages])

  // Auto scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (!videoId) {
    return (
      <div className="flex-1 flex items-center justify-center p-4">
        <p className="text-sm text-muted-foreground text-center">
          Select a video to start chatting.
        </p>
      </div>
    )
  }

  if (!isReady) {
    return (
      <div className="flex-1 flex items-center justify-center p-4">
        <p className="text-sm text-muted-foreground text-center">
          Chat will be available once the video is fully processed and indexed.
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b">
        <h2 className="text-sm font-semibold">Chat with Video</h2>
      </div>

      <ScrollArea className="flex-1 p-4">
        {messages.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center mt-8">
            Ask anything about this video.
          </p>
        ) : (
          messages.map((msg, idx) => (
            <MessageBubble key={idx} message={msg} />
          ))
        )}
        <div ref={bottomRef} />
      </ScrollArea>

      <ChatInput
        onSend={(question) => sendMessage(videoId, question)}
        disabled={isStreaming}
      />
    </div>
  )
}