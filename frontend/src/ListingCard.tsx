import { useState } from 'react'

import { formatPrice } from './format'
import { AGENCY_NAMES, type Listing } from './types'

interface ListingCardProps {
  listing: Listing
}

export function ListingCard({ listing }: ListingCardProps) {
  const [imageBroken, setImageBroken] = useState(false)
  const [copied, setCopied] = useState(false)

  // A broken image is a decent signal the listing has been delisted;
  // hide the card rather than show a link likely to 404.
  if (imageBroken) return null

  const handleShare = async () => {
    const shareData = { title: listing.title, url: listing.url }
    if (navigator.share) {
      try {
        await navigator.share(shareData)
      } catch {
        // User cancelled or share failed — nothing to do.
      }
      return
    }
    try {
      await navigator.clipboard.writeText(listing.url)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      // Clipboard unavailable — fail quietly.
    }
  }

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
      <button
        className="card-share"
        type="button"
        onClick={handleShare}
        aria-label={copied ? 'Link copied' : 'Share listing'}
      >
        {copied ? (
          <span className="card-share-label">Copied</span>
        ) : (
          <svg
            viewBox="0 0 24 24"
            width="16"
            height="16"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <circle cx="18" cy="5" r="3" />
            <circle cx="6" cy="12" r="3" />
            <circle cx="18" cy="19" r="3" />
            <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
            <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
          </svg>
        )}
      </button>
    </article>
  )
}
