import type { Listing } from '../types'

export type SortOption = 'newest' | 'price-asc' | 'price-desc'

export const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: 'newest', label: 'Newest' },
  { value: 'price-asc', label: 'Price ↑' },
  { value: 'price-desc', label: 'Price ↓' },
]

export function sortListings(listings: Listing[], sort: SortOption): Listing[] {
  const copy = [...listings]
  switch (sort) {
    case 'newest':
      return copy.sort(
        (a, b) => new Date(b.first_seen).getTime() - new Date(a.first_seen).getTime(),
      )
    case 'price-asc':
      return copy.sort((a, b) => a.price - b.price)
    case 'price-desc':
      return copy.sort((a, b) => b.price - a.price)
  }
}
