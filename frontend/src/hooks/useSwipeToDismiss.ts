import { type CSSProperties, useState } from 'react'
import { type SwipeableHandlers, useSwipeable } from 'react-swipeable'

interface UseSwipeToDismissResult {
  /** Spread onto the element that should be swipeable. */
  handlers: SwipeableHandlers
  /** Inline transform/opacity reflecting the in-progress drag, or undefined when idle. */
  style: CSSProperties | undefined
}

/** Horizontal drag distance past which a swipe counts as a dismiss. */
const SWIPE_THRESHOLD_PX = 80

/**
 * Makes an element swipeable left/right to dismiss it, with a live drag-follow
 * (the element tracks the finger and fades as it moves).
 *
 * :param onDismiss: Called once a swipe travels past the dismiss threshold.
 * :param enabled: When false, swipes are ignored — e.g. for an already-dismissed item.
 * :return: Handlers to spread onto the element, and the current drag style.
 */
export function useSwipeToDismiss(
  onDismiss: () => void,
  enabled: boolean,
): UseSwipeToDismissResult {
  const [dragX, setDragX] = useState(0)

  const handlers = useSwipeable({
    onSwiping: (e) => {
      if (!enabled) return
      if (e.dir === 'Left' || e.dir === 'Right') {
        setDragX(e.dir === 'Left' ? -e.absX : e.absX)
      }
    },
    onSwiped: (e) => {
      if (!enabled) return
      if ((e.dir === 'Left' || e.dir === 'Right') && e.absX > SWIPE_THRESHOLD_PX) {
        onDismiss()
      }
      setDragX(0)
    },
    trackMouse: false,
  })

  const style =
    dragX !== 0
      ? {
          transform: `translateX(${dragX}px)`,
          opacity: 1 - Math.min(Math.abs(dragX) / 240, 0.6),
        }
      : undefined

  return { handlers, style }
}
