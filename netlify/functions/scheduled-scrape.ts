import { triggerScrape } from './_trigger'

// Cron is widened to cover both BST (UTC+1) and GMT (UTC+0); the hour check
// below gates on London local time so DST transitions are handled automatically.
export default async () => {
  const londonHour = parseInt(
    new Intl.DateTimeFormat('en-GB', {
      timeZone: 'Europe/London',
      hour: 'numeric',
      hour12: false,
    }).format(new Date()),
    10,
  )

  if (londonHour < 8 || londonHour > 18) {
    return new Response('outside active hours', { status: 204 })
  }

  return triggerScrape()
}

export const config = {
  schedule: '0,30 7-18 * * *',
}
