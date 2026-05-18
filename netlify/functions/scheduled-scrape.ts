import { triggerScrape } from './_trigger'

export default async () => triggerScrape()

export const config = {
  schedule: '0,30 8-18 * * *',
}
