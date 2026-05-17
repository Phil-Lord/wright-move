import { ListingCard } from './ListingCard'
import { useListings } from './useListings'

function App() {
  const { listings, loading, error } = useListings()

  return (
    <>
      <header className="header">
        <h1>Wright Move</h1>
      </header>
      <main className="main">
        {loading && <p className="status">Loading…</p>}
        {error && <p className="status status-error">Failed to load: {error}</p>}
        {!loading && !error && listings.length === 0 && (
          <p className="status">No listings yet.</p>
        )}
        {!loading && !error && listings.length > 0 && (
          <div className="grid">
            {listings.map((listing) => (
              <ListingCard key={listing.id} listing={listing} />
            ))}
          </div>
        )}
      </main>
    </>
  )
}

export default App
