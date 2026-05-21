import { SORT_OPTIONS, type SortOption } from '../lib/sort'

interface HeaderProps {
  sort: SortOption
  onSortChange: (sort: SortOption) => void
  hiddenCount: number
  showHidden: boolean
  onToggleHidden: () => void
}

export function Header({
  sort,
  onSortChange,
  hiddenCount,
  showHidden,
  onToggleHidden,
}: HeaderProps) {
  return (
    <header className="header">
      <h1>Wright Move</h1>
      <div className="header-controls">
        {(hiddenCount > 0 || showHidden) && (
          <button
            className="toggle-hidden"
            type="button"
            onClick={onToggleHidden}
            aria-pressed={showHidden}
          >
            {showHidden ? 'Back to listings' : `Show hidden (${hiddenCount})`}
          </button>
        )}
        <label className="sort">
          <span className="sort-label">Sort by</span>
          <select
            className="sort-select"
            value={sort}
            onChange={(e) => onSortChange(e.target.value as SortOption)}
          >
            {SORT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>
    </header>
  )
}
