export type Agency = 'fss'

export interface Listing {
  id: string
  agency: Agency
  title: string
  price: number       // Pence
  bedrooms: number
  url: string
  image_url: string | null
  scraped_at: string  // ISO 8601 from Postgres timestampz
}
