"""Checks that the links in data/demo_examples.md are still live.

This used to also re-derive and check the stats in demo_examples.md, using
the matching logic in pick_demo_examples.py. That stopped being meaningful
once apps/backend existed: its matcher (progressive band-widening, see
services/matching.py) is the real, correct one, and doesn't agree with
pick_demo_examples.py's simpler fixed-band version. demo_examples.md is now
generated from the backend's actual /predict output, so the backend's own
test suite (apps/backend/tests) is what verifies the stats — this script
only checks the one thing specific to the data layer: do the closest-match
links still resolve.

    python data/verify_demo_examples.py
"""

from __future__ import annotations

import subprocess
import sys

# (council, [(id, link), ...]) — kept in sync with data/demo_examples.md by hand.
EXAMPLES = [
    (
        "South Dublin County Council",
        [
            ("S01A/0114", "https://planning.agileapplications.ie/southdublin/application-details/15357"),
            ("SDZ19A/0008", "https://planning.agileapplications.ie/southdublin/application-details/57034"),
            ("SDZ19A/0007", "https://planning.agileapplications.ie/southdublin/application-details/57033"),
            ("SD04A/0160", "https://planning.agileapplications.ie/southdublin/application-details/22552"),
            ("SD03A/0966", "https://planning.agileapplications.ie/southdublin/application-details/22081"),
        ],
    ),
    (
        "Kildare County Council",
        [
            ("21311040", "http://www.eplanning.ie/KildareCC/AppFileRefDetails/21311040/0"),
            ("20307013", "http://www.eplanning.ie/KildareCC/AppFileRefDetails/20307013/0"),
            ("181481", "http://www.eplanning.ie/KildareCC/AppFileRefDetails/181481/0"),
            ("22599", "http://www.eplanning.ie/KildareCC/AppFileRefDetails/22599/0"),
            ("2460371", "http://www.eplanning.ie/KildareCC/AppFileRefDetails/2460371/0"),
        ],
    ),
    (
        "Louth County Council",
        [
            ("201086", "http://www.eplanning.ie/LouthCC/AppFileRefDetails/201086/0"),
            ("211344", "http://www.eplanning.ie/LouthCC/AppFileRefDetails/211344/0"),
            ("2360494", "http://www.eplanning.ie/LouthCC/AppFileRefDetails/2360494/0"),
            ("211212", "http://www.eplanning.ie/LouthCC/AppFileRefDetails/211212/0"),
            ("2460772", "http://www.eplanning.ie/LouthCC/AppFileRefDetails/2460772/0"),
        ],
    ),
]


def check_links() -> bool:
    # Shells out to curl rather than using `requests`: Kildare's and Louth's
    # e-planning server (old IIS, TLS/HTTP negotiation) resets every
    # connection from Python's urllib3 but serves curl fine — and a browser
    # behaves like curl here, which is what actually matters for the demo.
    ok = True
    for council, matches in EXAMPLES:
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
    print("--- checking demo_examples.md links are live ---")
    if check_links():
        print("\nAll good — every link resolves.")
        print("Note: stats aren't checked here — run apps/backend's own test suite,")
        print("or POST the three inputs to a running /predict and compare by eye.")
    else:
        print("\nSomething's dead — see above. Update demo_examples.md with a working match.")
        sys.exit(1)


if __name__ == "__main__":
    main()
