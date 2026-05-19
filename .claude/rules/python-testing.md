# Python Testing Conventions

Reference for Python test code in this project. Universal style rules (Python 3.12+ syntax, single
quotes, British English, type hints) live in `CLAUDE.md` and apply here too.

---

## Layout

- **Unit tests** — `scraper/tests/unit/`, mirroring source structure
  (`agency/foo.py` → `tests/unit/agency/test_foo.py`).
- **Integration tests** — `scraper/tests/integration/` as flat files.
- `pytest.ini` sets `pythonpath = scraper` and `testpaths = scraper/tests`, so plain `pytest`
  works from the repo root.

---

## Naming

| Element     | Convention                                | Example                                      |
| ----------- | ----------------------------------------- | -------------------------------------------- |
| Test file   | `test_{module}.py`                        | `test_scraper.py`                            |
| Test class  | `Test{ClassName}`                         | `TestListing`                                |
| Test method | `test_{action}_{condition}_{expectation}` | `test_get_listings_none_when_not_found`      |

Test files import from the direct module path, not the package re-export, so cmd-click resolves
to the definition rather than the re-export.

---

## Structure

Use the **Given/When/Then** pattern with comments when the test benefits from the structure —
multi-step flows, non-trivial setup, or where the action/assertion boundary isn't obvious. Skip
the comments when the test is short and self-evident.

```python
def test_add_inserts_listings(self, mock_client, mock_session, sample_listing: Listing):
    # Given
    repository = ListingRepository(mock_client)

    # When
    repository.add([sample_listing])

    # Then
    mock_session.execute.assert_called_once()
```

```python
def test_listing_is_frozen(self, sample_listing_data):
    listing = Listing(**sample_listing_data)
    with pytest.raises(AttributeError):
        listing.price = 995.0
```

---

## Markers — hierarchical

Apply markers at three levels where needed for granular selection:

```python
@pytest.mark.data_system           # Module
@pytest.mark.repositories          # Category
@pytest.mark.listing_repository    # Class
class TestListingRepository:
    ...
```

**Every new marker must be registered in `pytest.ini`.** Look at the existing marker block to
see the conventions for descriptions.

Run subsets with marker expressions:

```bash
pytest -m data_system
pytest -m "data_system and repositories"
pytest -m integration
```

---

## Integration tests

**Mock only at system boundaries** (HTTP, database connections, file I/O). Let connectors,
services, clients, and transformations all run together. Catches layer-interaction bugs that
unit tests miss.

Markers: `@pytest.mark.integration` (top-level) plus `@pytest.mark.{module}_integration` for the
specific suite.

**Write integration tests when:**
- Multi-layer interactions need verifying (connector → service → client)
- Realistic API data flows through domain transformations
- Parameter passing across multiple function calls
- Error propagation from low-level errors to high-level handlers

**Don't write integration tests for** simple unit-level logic, individual methods in isolation,
or business logic that doesn't span layers.

**Common pitfalls:**
- Mock `time.sleep` so retry loops don't actually delay.
- Make pagination mocks return a terminating sentinel — infinite loops are easy.
- `isinstance(obj, list)` works; `isinstance(obj, list[Type])` does not.
- Account for service-level transformations applied before the result reaches the test
  (e.g. `[:-1]` slicing for pagination cursors).

---

## Coverage philosophy

Test **behaviour**, not just code paths.

- ✅ Retry logic, error propagation, pagination, validation edge cases
- ✅ Integration points between layers
- ❌ Happy-path-only tests with everything mocked
- ❌ Pure delegation (connector calling service with no transformation)

---

## Fixtures

- Define fixtures inside the test class when class-specific.
- Type-hint fixture return values.
- Use descriptive names: `sample_listing_data`, `mock_supabase_client`.

```python
@pytest.fixture
def sample_listing(self) -> Listing:
    return Listing(
        id=123456789,
        price=996.0,
        ...
    )
```

---

## Scraper fixtures

Hand-curate scraper fixtures (`tests/fixtures/`) down to the minimum needed for the
assertions — typically 2–3 stripped cards in a basic HTML/JSON shell. Don't commit raw
site dumps: they bloat the repo, leak content beyond fair-use needs, and make tests
harder to read. See `fss.html` and `linley_and_simpson.json` for the target shape.
