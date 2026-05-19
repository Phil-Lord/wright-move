import { SORT_OPTIONS, type SortOption } from '../lib/sort'

interface HeaderProps {
  sort: SortOption
  onSortChange: (sort: SortOption) => void
}

export function Header({ sort, onSortChange }: HeaderProps) {
  return (
    <header className="header">
      <h1>Wright Move</h1>
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
    </header>
  )
}
