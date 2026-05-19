const priceFormatter = new Intl.NumberFormat('en-GB', {
  style: 'currency',
  currency: 'GBP',
  maximumFractionDigits: 0,
})

export function formatPrice(pence: number): string {
  return `${priceFormatter.format(pence / 100)} pcm`
}

const relativeFormatter = new Intl.RelativeTimeFormat('en-GB', { numeric: 'auto' })

/**
 * Formats an ISO 8601 timestamp as a human-readable relative time,
 * e.g. 'just now', '12 minutes ago', '3 hours ago'.
 */
export function formatRelativeTime(iso: string): string {
  const diffMs = new Date(iso).getTime() - Date.now()
  const diffMins = Math.round(diffMs / 60_000)

  if (Math.abs(diffMins) < 1) return 'just now'
  if (Math.abs(diffMins) < 60) return relativeFormatter.format(diffMins, 'minute')

  const diffHours = Math.round(diffMins / 60)
  if (Math.abs(diffHours) < 24) return relativeFormatter.format(diffHours, 'hour')

  return relativeFormatter.format(Math.round(diffHours / 24), 'day')
}
