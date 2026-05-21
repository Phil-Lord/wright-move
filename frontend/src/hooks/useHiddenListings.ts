import { useCallback, useEffect, useState } from 'react'

const STORAGE_KEY = 'wm:hidden-listings'

interface UseHiddenListingsResult {
  /** Set of listing ids the user has dismissed. */
  hiddenIds: ReadonlySet<string>
  hide: (id: string) => void
  unhide: (id: string) => void
}

/** Reads the persisted id list, tolerating missing or corrupt storage. */
function readStored(): string[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed: unknown = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed.filter((x): x is string => typeof x === 'string')
  } catch {
    return []
  }
}

/**
 * Tracks listings the user has manually hidden, persisted to localStorage.
 *
 * State is per-browser (no accounts) — hiding on one device does not sync to
 * another. Only ids are stored, so a hidden listing later vanishing from the
 * DB simply leaves a harmless stale id in the set.
 */
export function useHiddenListings(): UseHiddenListingsResult {
  const [hiddenIds, setHiddenIds] = useState<Set<string>>(() => new Set(readStored()))

  // Mirror the set to localStorage whenever it changes.
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify([...hiddenIds]))
    } catch {
      // localStorage unavailable (private mode / quota) — hidden state stays
      // in-memory for this session only.
    }
  }, [hiddenIds])

  const hide = useCallback((id: string) => {
    setHiddenIds((prev) => {
      if (prev.has(id)) return prev
      const next = new Set(prev)
      next.add(id)
      return next
    })
  }, [])

  const unhide = useCallback((id: string) => {
    setHiddenIds((prev) => {
      if (!prev.has(id)) return prev
      const next = new Set(prev)
      next.delete(id)
      return next
    })
  }, [])

  return { hiddenIds, hide, unhide }
}
