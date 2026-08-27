import re

_STRIP_HYPHENS_SPACES = re.compile(r'[- ]')


def _isbn10_checksum_valid(isbn10):
    total = 0
    for i, ch in enumerate(isbn10):
        if ch == 'X' and i == 9:
            value = 10
        elif ch.isdigit():
            value = int(ch)
        else:
            return False
        total += value * (10 - i)
    return total % 11 == 0


def _isbn13_checksum_valid(isbn13):
    if not isbn13.isdigit():
        return False
    total = sum(
        int(digit) * (1 if i % 2 == 0 else 3)
        for i, digit in enumerate(isbn13)
    )
    return total % 10 == 0


def _isbn10_to_isbn13(isbn10):
    core = '978' + isbn10[:9]
    total = sum(
        int(digit) * (1 if i % 2 == 0 else 3)
        for i, digit in enumerate(core)
    )
    check_digit = (10 - (total % 10)) % 10
    return core + str(check_digit)


def normalize_isbn(raw_value):
    """
    Accepts an ISBN-10 or ISBN-13, with or without hyphens/spaces
    (e.g. from an external books API). Validates its checksum and
    returns a normalized, hyphen-free ISBN-13 string.

    Raises ValueError with a human-readable message if invalid, so the
    caller (a serializer) can turn it into a proper ValidationError.
    """
    cleaned = _STRIP_HYPHENS_SPACES.sub('', raw_value).upper()

    if len(cleaned) == 10:
        if not _isbn10_checksum_valid(cleaned):
            raise ValueError("Invalid ISBN-10 checksum.")
        return _isbn10_to_isbn13(cleaned)

    if len(cleaned) == 13:
        if not _isbn13_checksum_valid(cleaned):
            raise ValueError("Invalid ISBN-13 checksum.")
        return cleaned

    raise ValueError("ISBN must be 10 or 13 characters (hyphens/spaces are ignored).")