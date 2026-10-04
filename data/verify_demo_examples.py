"""Checks that data/demo_examples.md still tells the truth.

Two things can go stale: the numbers (if applications.parquet is regenerated
from a refreshed source) and the links (if a council's e-planning system
moves a page). This re-derives the three examples' stats from the real table
and re-checks the stats are what's written in demo_examples.md, then pings
every "closest match" link to confirm it still resolves.

Run before you rehearse, and again right before the demo if there's time:

    python data/verify_demo_examples.py
"""

from __future__ import annotations

import subprocess
import sys

import pandas as pd

from pick_demo_examples import match, summarise

# (council, units, storeys, expected stats, [(id, link), ...])
# Expected values are what's written in demo_examples.md — kept in sync by hand.
EXAMPLES = [
    (
        "South Dublin County Council", 150, 10,
        {"n_decided": 78, "grant_rate": 0.83, "median_weeks": 7.3},
        [
            ("SHD3ABP-312430-22", "https://planning.agileapplications.ie/southdublin/application-details/61773"),
            ("SD26A/0184W", "https://planning.agileapplications.ie/southdublin/application-details/70736"),
            ("SDZ21A/0007", "https://planning.agileapplications.ie/southdublin/application-details/60624"),
        ],
    ),
    (
        "Kildare County Council", 90, 6,
        {"n_decided": 20, "grant_rate": 0.75, "median_weeks": 32.4},
        [
            ("211606", "http://www.eplanning.ie/KildareCC/AppFileRefDetails/211606/0"),
            ("2560988", "http://www.eplanning.ie/KildareCC/AppFileRefDetails/2560988/0"),
            ("18301818", "http://www.eplanning.ie/KildareCC/AppFileRefDetails/18301818/0"),
        ],
    ),
    (
        "Louth County Council", 60, 5,
        {"n_decided": 31, "grant_rate": 0.81, "median_weeks": 23.0},
        [
            ("201086", "http://www.eplanning.ie/LouthCC/AppFileRefDetails/201086/0"),
            ("211344", "http://www.eplanning.ie/LouthCC/AppFileRefDetails/211344/0"),
            ("2360494", "http://www.eplanning.ie/LouthCC/AppFileRefDetails/2360494/0"),
        ],
    ),
]


def check_stats(df: pd.DataFrame) -> bool:
    ok = True
    for council, units, storeys, expected, _ in EXAMPLES:
        actual = summarise(match(df, council, units, storeys))
        for key, expected_value in expected.items():
            actual_value = actual.get(key)
            if actual_value != expected_value:
                ok = False
                print(f"STALE  {council} {units}u/{storeys}s: {key} is now {actual_value}, "
                      f"demo_examples.md says {expected_value}")
        if ok:
            print(f"ok     {council} {units}u/{storeys}s stats match demo_examples.md")
    return ok


def check_links() -> bool:
    # Shells out to curl rather than using `requests`: at least one council's
    # e-planning server (IIS, old-style TLS/HTTP negotiation) resets every
    # connection from Python's urllib3 but serves curl — and a browser
    # behaves like curl here, which is what actually matters for the demo.
    ok = True
    for council, _, _, _, matches in EXAMPLES:
        for app_id, link in matches:
            try:
                result = subprocess.run(
                    ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                     "-L", "--max-time", "15", link],
                    capture_output=True, text=True, check=False,
                )
                code = int(result.stdout.strip() or "0")
            except (subprocess.SubprocessError, ValueError) as exc:
                print(f"DEAD   {council} {app_id}: {link} -> {exc}")
                ok = False
                continue
            status = "ok" if 200 <= code < 400 else "DEAD"
            print(f"{status:<6} {council} {app_id}: {link} -> HTTP {code}")
            if not (200 <= code < 400):
                ok = False
    return ok


def main() -> None:
    df = pd.read_parquet("data/applications.parquet")
    print("--- checking stats against demo_examples.md ---")
    stats_ok = check_stats(df)
    print("\n--- checking links are live ---")
    links_ok = check_links()

    print()
    if stats_ok and links_ok:
        print("All good — demo_examples.md is accurate and every link resolves.")
    else:
        print("Something's stale — see above. Update demo_examples.md or swap the broken link.")
        sys.exit(1)


if __name__ == "__main__":
    main()
