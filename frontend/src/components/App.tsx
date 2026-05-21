import { DotLottieReact } from '@lottiefiles/dotlottie-react'
import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'

import loadingDog from '../assets/loading-dog.lottie?url'
import { useHiddenListings } from '../hooks/useHiddenListings'
import { useListings } from '../hooks/useListings'
import { formatRelativeTime } from '../lib/format'
import { sortListings, type SortOption } from '../lib/sort'
import type { Listing } from '../types'
import { Header } from './Header'
import { ListingCard } from './ListingCard'

/** How long the undo prompt stays on screen after hiding a listing. */
const UNDO_TIMEOUT_MS = 6000

/** The loading dog paired with a message, used for empty and error states. */
function DogMessage({ children }: { children: ReactNode }) {
  return (
    <div className="dog-message">
      <DotLottieReact
        className="dog-animation"
        src={loadingDog}
        loop
        autoplay
      />
      <p className="status">{children}</p>
    </div>
  )
}

function App() {
  const { listings, loading, error } = useListings()
  const { hiddenIds, hide, unhide } = useHiddenListings()
  const [sort, setSort] = useState<SortOption>('newest')
  const [showHidden, setShowHidden] = useState(false)
  const [pendingUndo, setPendingUndo] = useState<Listing | null>(null)

  const visibleListings = useMemo(() => {
    const filtered = listings.filter((l) =>
      showHidden ? hiddenIds.has(l.id) : !hiddenIds.has(l.id),
    )
    return sortListings(filtered, sort)
  }, [listings, hiddenIds, showHidden, sort])

  const hiddenCount = useMemo(
    () => listings.reduce((count, l) => (hiddenIds.has(l.id) ? count + 1 : count), 0),
    [listings, hiddenIds],
  )

  const lastUpdated = useMemo(() => {
    if (listings.length === 0) return null
    const latest = listings.reduce(
      (max, l) => Math.max(max, new Date(l.last_seen).getTime()),
      0,
    )
    return new Date(latest).toISOString()
  }, [listings])

  const handleHide = useCallback(
    (listing: Listing) => {
      hide(listing.id)
      setPendingUndo(listing)
    },
    [hide],
  )

  const handleUnhide = useCallback(
    (listing: Listing) => {
      unhide(listing.id)
      setPendingUndo(null)
    },
    [unhide],
  )

  const handleUndo = useCallback(() => {
    if (pendingUndo) unhide(pendingUndo.id)
    setPendingUndo(null)
  }, [pendingUndo, unhide])

  // Auto-dismiss the undo prompt after a few seconds.
  useEffect(() => {
    if (!pendingUndo) return
    const timer = setTimeout(() => setPendingUndo(null), UNDO_TIMEOUT_MS)
    return () => clearTimeout(timer)
  }, [pendingUndo])

  return (
    <>
      <Header
        sort={sort}
        onSortChange={setSort}
        hiddenCount={hiddenCount}
        showHidden={showHidden}
        onToggleHidden={() => setShowHidden((v) => !v)}
      />
      <main className="main">
        {loading && (
          <div className="loading">
            <DotLottieReact
              className="dog-animation"
              src={loadingDog}
              loop
              autoplay
            />
          </div>
        )}
        {error && (
          <DogMessage>
            Something went wrong fetching listings. Try again in a bit — {error}
          </DogMessage>
        )}
        {!loading && !error && visibleListings.length === 0 && (
          <DogMessage>Woofing to see here...</DogMessage>
        )}
        {!loading && !error && visibleListings.length > 0 && (
          <>
            <p className="summary">
              {visibleListings.length}{' '}
              {showHidden
                ? visibleListings.length === 1
                  ? 'hidden listing'
                  : 'hidden listings'
                : visibleListings.length === 1
                  ? 'listing'
                  : 'listings'}
              {!showHidden && lastUpdated && ` · updated ${formatRelativeTime(lastUpdated)}`}
            </p>
            <div className="grid">
              {visibleListings.map((listing) => (
                <ListingCard
                  key={listing.id}
                  listing={listing}
                  hidden={showHidden}
                  onHide={handleHide}
                  onUnhide={handleUnhide}
                />
              ))}
            </div>
          </>
        )}
      </main>
      {pendingUndo && (
        <div className="toast" role="status">
          <span className="toast-text">Hidden “{pendingUndo.title}”</span>
          <button className="toast-undo" type="button" onClick={handleUndo}>
            Undo
          </button>
        </div>
      )}
    </>
  )
}

export default App
