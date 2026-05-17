import { useEffect, useState } from 'react'

import { supabase } from './supabase'
import type { Listing } from './types'

interface UseListingsResult {
  listings: Listing[]
  loading: boolean
  error: string | null
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
          setListings(data as Listing[])
        }
        setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  return { listings, loading, error }
}
