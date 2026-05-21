import { useState } from 'react'

import { useSwipeToDismiss } from '../hooks/useSwipeToDismiss'
import { formatPrice } from '../lib/format'
import { AGENCY_NAMES, type Listing } from '../types'
import { ShareButton } from './ShareButton'

interface ListingCardProps {
  listing: Listing
  /** Whether this card is being shown in the hidden-listings view. */
  hidden: boolean
  onHide: (listing: Listing) => void
  onUnhide: (listing: Listing) => void
}

export function ListingCard({ listing, hidden, onHide, onUnhide }: ListingCardProps) {
  const [imageBroken, setImageBroken] = useState(false)

  // Swipe-to-dismiss on touch devices; the ✕ button is the desktop equivalent.
  // Disabled for already-hidden cards — there is nothing to swipe away.
  const { handlers: swipeHandlers, style: dragStyle } = useSwipeToDismiss(
    () => onHide(listing),
    !hidden,
  )

  // A broken image is a decent signal the listing has been delisted;
  // hide the card rather than show a link likely to 404.
  if (imageBroken) return null

  return (
    <article
      className={hidden ? 'card card-is-hidden' : 'card'}
      {...swipeHandlers}
      style={dragStyle}
    >
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
      <button
        className="card-dismiss"
        type="button"
        onClick={() => (hidden ? onUnhide(listing) : onHide(listing))}
        aria-label={hidden ? 'Restore listing' : 'Hide listing'}
      >
        {hidden ? 'Restore' : '✕'}
      </button>
    </article>
  )
}
