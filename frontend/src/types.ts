export type Agency = 'fss' | 'linley_and_simpson' | 'verity_frearson'

export const AGENCY_NAMES: Record<Agency, string> = {
  fss: 'FSS',
  linley_and_simpson: 'Linley & Simpson',
  verity_frearson: 'Verity Frearson',
}

export interface Listing {
  id: string
  agency: Agency
  title: string
  price: number       // Pence
  bedrooms: number
  url: string
  image_url: string | null
  first_seen: string  // ISO 8601 — when the scraper first saw this listing
  last_seen: string   // ISO 8601 — most recent scrape that saw this listing
}
