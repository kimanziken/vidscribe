import { useState, useCallback } from 'react'
import { streamChat } from '@/api/client'
import type { ChatMessage } from '@/types'

export function useStream() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)

  const sendMessage = useCallback(async (videoId: string, question: string) => {
    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: question }])

    // Add empty assistant message that we'll stream into
    setMessages(prev => [...prev, { role: 'assistant', content: '', streaming: true }])
    setIsStreaming(true)

    try {
      await streamChat(
        videoId,
        question,
        (token) => {
          setMessages(prev => {
            const updated = [...prev]
            const last = updated[updated.length - 1]
            updated[updated.length - 1] = {
              ...last,
              content: last.content + token,
            }
            return updated
          })
        },
        () => {
          setMessages(prev => {
            const updated = [...prev]
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              streaming: false,
            }
            return updated
          })
          setIsStreaming(false)
        }
      )
    } catch (err) {
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = {
          role: 'assistant',
          content: 'Error getting response. Please try again.',
          streaming: false,
        }
        return updated
      })
      setIsStreaming(false)
    }
  }, [])

  const clearMessages = useCallback(() => {
    setMessages([])
  }, [])

  return { messages, isStreaming, sendMessage, clearMessages }
}