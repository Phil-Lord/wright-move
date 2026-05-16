# Python Docstring Conventions

Reference for when and how to write docstrings in this project.

---

## When to write a docstring

**Required:**

- **Domain models (frozen dataclasses)** — Document every attribute in the class docstring.
- **Public API functions and methods** — Repository methods, service entry points, anything
  re-exported from a module's `__init__.py`.
- **Complex logic** — Anything where the WHY isn't obvious from reading the code.
- **Non-obvious parameters** — Document units (nanoseconds vs seconds) or unusual contracts.

**Skip:**

- **Constants and config values** — The name says it.
- **Simple utility functions** — If the signature and name are clear, a docstring is noise.
- **Internal helpers** — Short private functions with obvious purpose.
- **Simple exception classes** — `ScraperTooManyRequestsError` doesn't need elaboration.
- **Pure delegation** — Methods that just call another method with the same semantics.

**Rule of thumb:** if the docstring would be slower to read than the code, skip it.

---

## Style — reStructuredText

Use `:param`, `:return:` format:

```python
def get(self, price: float, time_added: float = None) -> list[Letting]:
    '''
    Fetches lettings from an agency below a certain price.

    :param price: Maximum price for the lettings.
    :param time_added: Timestamp for when the letting was added. If None, fetches all.
    :return: List of Letting domain objects.
    '''
```

For dataclasses, document attributes in the class docstring:

```python
@dataclass(frozen=True)
class Letting:
    '''
    Dataclass representing a single letting from the agency.

    Attributes:
        letting_id (str): Unique letting identifier from the agency.
        price (float): Price of the letting.
        ...

    Note:
        Primary key is composite (letting_id, price) since letting IDs are only
        unique per price on the agency's platform (this is just an example).
    '''
    letting_id: str
    price: float
    ...
```

Single quotes for docstrings (consistent with the rest of the codebase).