"""Quick checks for the pure logic in prep.py / tag_descriptions.py.

No network, no pandas DataFrame needed — just the string/date functions
that are easiest to get subtly wrong. Run with:

    python data/test_pipeline.py

Exits non-zero on the first failure so it's safe to chain in a shell script.
"""

from __future__ import annotations

from prep import normalise_decision
from tag_descriptions import extract_mixed_use, extract_storeys, extract_units

CASES_RUN = 0
CASES_FAILED = 0


def check(label: str, actual, expected) -> None:
    global CASES_RUN, CASES_FAILED
    CASES_RUN += 1
    if actual != expected:
        CASES_FAILED += 1
        print(f"FAIL  {label}: got {actual!r}, expected {expected!r}")
    else:
        print(f"ok    {label}")


def test_normalise_decision() -> None:
    # Real values seen live in the Decision field (see data/schema.md).
    check("grant plain", normalise_decision("Grant Permission              "), "granted")
    check("grant caps", normalise_decision("GRANT PERMISSION"), "granted")
    check("refuse", normalise_decision("REFUSED"), "refused")
    check("refuse retention", normalise_decision("REFUSE RETENTION PERMISSION"), "refused")
    check("split grant+refuse -> granted", normalise_decision("Grant Permission & Refuse Retention"), "granted")
    check("withdrawn", normalise_decision("APPLICATION WITHDRAWN"), "withdrawn")
    check("withdrawn mixed case", normalise_decision("App withdrawn as no AI recd in 6 months"), "withdrawn")
    check("invalid", normalise_decision("DECLARE APPLICATION INVALID"), "invalid")
    check("invalid short", normalise_decision("Invalid - Site Notice"), "invalid")
    check("non-final excluded", normalise_decision("N/A"), None)
    check("additional info excluded", normalise_decision("ADDITIONAL INFORMATION"), None)
    check("blank excluded", normalise_decision(""), None)
    check("none input", normalise_decision(None), None)
    check("part 8 approved -> granted", normalise_decision("Part 8 Approved by Council"), "granted")
    check("part 8 rejected -> refused", normalise_decision("Part 8 Rejected by Council"), "refused")


def test_extract_storeys() -> None:
    check("digit storey", extract_storeys("an 8-storey block"), 8)
    check("digit story (US spelling)", extract_storeys("a 3 story building"), 3)
    check("word number", extract_storeys("an eight-storey block"), 8)
    check("no mention", extract_storeys("demolition of existing shed"), None)
    check("non-string input", extract_storeys(None), None)  # type: ignore[arg-type]


def test_extract_mixed_use() -> None:
    check("ground floor retail", extract_mixed_use("120 apartments with ground-floor retail"), True)
    check("mixed use phrase", extract_mixed_use("a mixed-use development"), True)
    check("plain residential", extract_mixed_use("45 apartments and associated site works"), False)


def test_extract_units() -> None:
    check("N apartments", extract_units("construction of 120 apartments"), 120)
    check("N no. apartments", extract_units("2 no. apartments for short term letting"), 2)
    check("N units", extract_units("88 residential units"), 88)
    check("no number", extract_units("change of use to apartment"), None)


def main() -> None:
    test_normalise_decision()
    test_extract_storeys()
    test_extract_mixed_use()
    test_extract_units()
    print(f"\n{CASES_RUN - CASES_FAILED}/{CASES_RUN} passed")
    if CASES_FAILED:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
