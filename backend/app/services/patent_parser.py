import re
from dataclasses import dataclass

PATENT_PATTERNS = [
    re.compile(
        r"^(?P<country>CN)(?P<number>\d{7,9})(?P<kind>[ABUYSP])$", re.IGNORECASE
    ),
    re.compile(
        r"^(?P<country>US)(?P<number>\d{6,8})(?P<kind>B[12]|A\d?|E\d?)$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?P<country>EP)(?P<number>\d{6,8})(?P<kind>[AB]\d?)$", re.IGNORECASE
    ),
    re.compile(
        r"^(?P<country>WO)(?P<year>\d{4})(?P<number>\d{6})(?P<kind>A[123]?)$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?P<country>JP)(?P<year>\d{4})-(?P<number>\d{6})(?P<kind>[ABUY])$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?P<country>JP)(?P<number>\d{9,11})(?P<kind>[ABUY])$", re.IGNORECASE
    ),
    re.compile(
        r"^(?P<country>KR)(?P<number>\d{7,9})(?P<kind>[ABUY])$", re.IGNORECASE
    ),
    re.compile(
        r"^(?P<country>DE)(?P<number>\d{8,10})(?P<kind>[ABCU])$", re.IGNORECASE
    ),
    re.compile(
        r"^(?P<country>GB)(?P<number>\d{7,8})(?P<kind>[AB])$", re.IGNORECASE
    ),
    re.compile(
        r"^(?P<country>FR)(?P<number>\d{7,8})(?P<kind>[AB])$", re.IGNORECASE
    ),
    re.compile(
        r"^(?P<country>TW)(?P<number>\d{6,8})(?P<kind>[ABUY])$", re.IGNORECASE
    ),
    re.compile(
        r"^(?P<country>IN)(?P<number>\d{6,8})(?P<kind>[AB])$", re.IGNORECASE
    ),
]

COUNTRY_MAP = {
    "CN": "China",
    "US": "United States",
    "EP": "European Patent Office",
    "WO": "PCT (WIPO)",
    "JP": "Japan",
    "KR": "South Korea",
    "DE": "Germany",
    "GB": "United Kingdom",
    "FR": "France",
    "TW": "Taiwan",
    "IN": "India",
}


@dataclass
class ParsedPatentNumber:
    raw: str
    country: str
    country_name: str
    number: str
    kind: str | None
    is_valid: bool
    error: str | None = None


def parse_patent_number(raw: str) -> ParsedPatentNumber:
    cleaned = raw.strip().upper().replace(" ", "").replace("-", "")

    for pattern in PATENT_PATTERNS:
        match = pattern.match(cleaned)
        if match:
            groups = match.groupdict()
            return ParsedPatentNumber(
                raw=raw.strip(),
                country=groups["country"],
                country_name=COUNTRY_MAP.get(
                    groups["country"], groups["country"]
                ),
                number=groups.get("full_number", groups.get("number", "")),
                kind=groups.get("kind"),
                is_valid=True,
            )

    generic_match = re.match(
        r"^(?P<country>[A-Z]{2})(?P<number>\d{5,12})(?P<kind>[A-Z]\d?)?$", cleaned
    )
    if generic_match:
        groups = generic_match.groupdict()
        return ParsedPatentNumber(
            raw=raw.strip(),
            country=groups["country"],
            country_name=COUNTRY_MAP.get(groups["country"], "Unknown"),
            number=groups["number"],
            kind=groups.get("kind"),
            is_valid=True,
        )

    return ParsedPatentNumber(
        raw=raw.strip(),
        country="",
        country_name="",
        number="",
        kind=None,
        is_valid=False,
        error=f"Unrecognized patent number format: {raw}",
    )


def normalize_patent_number(raw: str) -> str:
    return raw.strip().upper().replace(" ", "")
