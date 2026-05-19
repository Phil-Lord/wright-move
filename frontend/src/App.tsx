import { useMemo, useState } from 'react'

import { Header } from './Header'
import { ListingCard } from './ListingCard'
import { sortListings, type SortOption } from './sort'
import { useListings } from './useListings'

function App() {
  const { listings, loading, error } = useListings()
  const [sort, setSort] = useState<SortOption>('newest')

  const sortedListings = useMemo(() => sortListings(listings, sort), [listings, sort])

  return (
    <>
      <Header sort={sort} onSortChange={setSort} />
      <main className="main">
        {loading && <p className="status">Loading…</p>}
        {error && <p className="status status-error">Failed to load: {error}</p>}
        {!loading && !error && sortedListings.length === 0 && (
          <p className="status">No listings yet.</p>
        )}
        {!loading && !error && sortedListings.length > 0 && (
          <div className="grid">
            {sortedListings.map((listing) => (
              <ListingCard key={listing.id} listing={listing} />
            ))}
          </div>
        )}
      </main>
    </>
  )
}

export default App
