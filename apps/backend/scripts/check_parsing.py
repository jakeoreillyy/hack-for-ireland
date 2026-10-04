"""Measure how well description parsing works on realistic inputs.

    python scripts/check_parsing.py          regex only (no key needed)
    python scripts/check_parsing.py --llm    full pipeline: regex first, then Claude where needed
                                             (needs ANTHROPIC_API_KEY in apps/backend/.env)

Each case is (description, expected units, expected storeys, expected mixed_use). Add real
descriptions from the data as Person 1's file arrives.
"""

import argparse

from planning_predictor.config import Settings
from planning_predictor.services.parsing import parse_description, parse_with_regex

CASES = [
    (
        "120 apartments in an 8-storey block near Heuston Station, with ground-floor retail",
        120,
        8,
        True,
    ),
    ("Construction of 64 no. apartments and a creche", 64, None, True),
    ("a nine storey building containing 210 apartments", 210, 9, False),
    (
        "Demolition of 2 houses and construction of 45 apartments in 2 blocks of 4 and 5 storeys",
        45,
        5,
        False,
    ),
    (
        "Mixed-use development of 300 apartments, a supermarket and offices up to 12 storeys",
        300,
        12,
        True,
    ),
    ("Build-to-rent scheme: 4 blocks of 30 apartments each", 120, None, False),
    ("Change of use of offices to 18 residential units", 18, None, False),
    ("seventeen-storey tower with 150 homes and a cafe at ground level", 150, 17, True),
    ("1,250 dwellings across ten blocks", 1250, None, False),
    ("Student accommodation of 400 bed spaces", None, None, False),
    ("6 storey apartment block", None, 6, False),
    ("A block of flats", None, None, False),
    (
        "Extension to existing apartment building, adding 12 flats on floors 5 and 6",
        12,
        None,
        False,
    ),
    ("Development of 80 houses and 24 apartments", 104, None, False),
    ("Three storey over basement residential block of 22 units", 22, 3, False),
    ("Proposed 5 to 7 storey development comprising 96 apartments and retail units", 96, 7, True),
    (
        "Alterations to approved 55 apartment scheme (ref 19/123) to increase to 61 apartments",
        61,
        None,
        False,
    ),
    ("14 storey tower, 168 residential units, commercial space at ground floor", 168, 14, True),
    ("Conversion of hotel to 40 apartments", 40, None, False),
    ("Social housing scheme, 36 homes, two storey terraces", 36, 2, False),
]
FIELDS = ("units", "storeys", "mixed_use")


def run(use_llm: bool) -> None:
    settings = Settings() if use_llm else Settings(_env_file=None, anthropic_api_key=None)
    if use_llm and not settings.anthropic_api_key:
        raise SystemExit("--llm needs ANTHROPIC_API_KEY set in apps/backend/.env")

    complete = field_hits = 0
    for text, *expected in CASES:
        regex = parse_with_regex(text)
        complete += regex.units is not None and regex.storeys is not None
        got, warnings = parse_description(text, None, settings)
        for name, want in zip(FIELDS, expected, strict=True):
            have = getattr(got, name)
            field_hits += have == want
            if have != want:
                print(f"MISS {name}: want {want}, got {have}\n     {text}")
        if any("unavailable" in w for w in warnings):
            print(f"LLM FAILED: {text}")

    mode = "regex + Claude" if use_llm else "regex only"
    total = len(CASES) * len(FIELDS)
    print(f"\n{mode}: {field_hits}/{total} fields correct over {len(CASES)} descriptions")
    print(
        f"Regex alone found both units and storeys in {complete}/{len(CASES)} "
        "(the rest would call Claude)"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--llm", action="store_true", help="also call Claude where regex is incomplete"
    )
    run(parser.parse_args().llm)
