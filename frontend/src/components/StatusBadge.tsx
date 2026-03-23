import { Badge } from '@/components/ui/badge'
import type { JobStatus } from '@/types'

const STATUS_CONFIG: Record<JobStatus, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }> = {
  uploaded: { label: 'Uploaded', variant: 'secondary' },
  extracting_audio: { label: 'Extracting', variant: 'secondary' },
  transcribing: { label: 'Transcribing', variant: 'secondary' },
  indexing: { label: 'Indexing', variant: 'secondary' },
  summarizing: { label: 'Summarizing', variant: 'secondary' },
  done: { label: 'Done', variant: 'default' },
  failed: { label: 'Failed', variant: 'destructive' },
}

interface StatusBadgeProps {
  status: JobStatus
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status]
  return (
    <Badge variant={config.variant}>
      {config.label}
    </Badge>
  )
}