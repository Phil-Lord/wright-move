import { DotLottieReact } from '@lottiefiles/dotlottie-react'
import { useMemo, useState } from 'react'

import loadingDog from '../assets/loading-dog.lottie?url'
import { useListings } from '../hooks/useListings'
import { sortListings, type SortOption } from '../lib/sort'
import { Header } from './Header'
import { ListingCard } from './ListingCard'

function App() {
  const { listings, loading, error } = useListings()
  const [sort, setSort] = useState<SortOption>('newest')

  const sortedListings = useMemo(() => sortListings(listings, sort), [listings, sort])

  return (
    <>
      <Header sort={sort} onSortChange={setSort} />
      <main className="main">
        {loading && (
          <div className="loading">
            <DotLottieReact
              src={loadingDog}
              loop
              autoplay
              style={{ width: 650, height: 650 }}
            />
          </div>
        )}
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
