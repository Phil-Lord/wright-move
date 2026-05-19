import { useState } from 'react'

import { formatPrice } from './format'
import { ShareButton } from './ShareButton'
import { AGENCY_NAMES, type Listing } from './types'

interface ListingCardProps {
  listing: Listing
}

export function ListingCard({ listing }: ListingCardProps) {
  const [imageBroken, setImageBroken] = useState(false)

  // A broken image is a decent signal the listing has been delisted;
  // hide the card rather than show a link likely to 404.
  if (imageBroken) return null

  return (
    <article className="card">
      {listing.image_url ? (
        <img
          className="card-image"
          src={listing.image_url}
          alt=""
          loading="lazy"
          onError={() => setImageBroken(true)}
        />
      ) : (
        <div className="card-image card-image-placeholder">{AGENCY_NAMES[listing.agency]}</div>
      )}
      <div className="card-body">
        <div className="card-price">{formatPrice(listing.price)}</div>
        <h2 className="card-title">
          <a
            className="card-link"
            href={listing.url}
            target="_blank"
            rel="noopener noreferrer"
          >
            {listing.title}
          </a>
        </h2>
        <div className="card-meta">
          <span>{listing.bedrooms} bed</span>
          <span className="card-agency">{AGENCY_NAMES[listing.agency]}</span>
        </div>
      </div>
      <ShareButton className="card-share" url={listing.url} title={listing.title} />
    </article>
  )
}
