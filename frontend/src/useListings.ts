import { useEffect, useState } from 'react'

import { supabase } from './supabase'
import type { Listing } from './types'

interface UseListingsResult {
  listings: Listing[]
  loading: boolean
  error: string | null
}

const FRESHNESS_WINDOW_MS = 60 * 60 * 1000

/**
 * Filters listings to only include those scraped within the last hour.
 *
 * The window is relative to the most recent scraped_at across all rows,
 * so the filter survives overnight gaps when no scrapes run.
 */
function filterFresh(listings: Listing[]): Listing[] {
  if (listings.length === 0) return listings
  const latestListingScrapedAt = listings.reduce(
    (max, l) => Math.max(max, new Date(l.scraped_at).getTime()),
    0,
  )
  const cutoff = latestListingScrapedAt - FRESHNESS_WINDOW_MS
  return listings.filter((l) => new Date(l.scraped_at).getTime() >= cutoff)
}

export function useListings(): UseListingsResult {
  const [listings, setListings] = useState<Listing[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    supabase
      .from('listings')
      .select('*')
      .order('price', { ascending: true })
      .then(({ data, error }) => {
        if (cancelled) return
        if (error) {
          setError(error.message)
        } else {
          setListings(filterFresh(data as Listing[]))
        }
        setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  return { listings, loading, error }
}
