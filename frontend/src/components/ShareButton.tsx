import { useState } from 'react'

interface ShareButtonProps {
  url: string
  title: string
  className?: string
}

export function ShareButton({ url, title, className }: ShareButtonProps) {
  const [copied, setCopied] = useState(false)

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({ url, title })
      } catch {
        // User cancelled or share failed — nothing to do.
      }
      return
    }
    try {
      await navigator.clipboard.writeText(url)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      // Clipboard unavailable — fail quietly.
    }
  }

  return (
    <button
      className={className}
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
  )
}
