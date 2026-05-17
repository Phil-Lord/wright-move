import { formatPrice } from './format'
import type { Listing } from './types'

interface ListingCardProps {
  listing: Listing
}

export function ListingCard({ listing }: ListingCardProps) {
  return (
    <a
      className="card"
      href={listing.url}
      target="_blank"
      rel="noopener noreferrer"
    >
      {listing.image_url ? (
        <img className="card-image" src={listing.image_url} alt="" loading="lazy" />
      ) : (
        <div className="card-image card-image-placeholder">{listing.agency}</div>
      )}
      <div className="card-body">
        <div className="card-price">{formatPrice(listing.price)}</div>
        <h2 className="card-title">{listing.title}</h2>
        <div className="card-meta">
          <span>{listing.bedrooms} bed</span>
          <span className="card-agency">{listing.agency}</span>
        </div>
      </div>
    </a>
  )
}
