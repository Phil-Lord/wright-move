export type Agency =
  | 'belvoir'
  | 'fss'
  | 'lentin_smith'
  | 'linley_and_simpson'
  | 'martin_and_co'
  | 'verity_frearson'
  | 'whitaker_cadre'
  | 'william_h_brown'

export const AGENCY_NAMES: Record<Agency, string> = {
  belvoir: 'Belvoir',
  fss: 'FSS',
  lentin_smith: 'Lentin Smith',
  linley_and_simpson: 'Linley & Simpson',
  martin_and_co: 'Martin & Co',
  verity_frearson: 'Verity Frearson',
  whitaker_cadre: 'Whitaker Cadre',
  william_h_brown: 'William H Brown',
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
