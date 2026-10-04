"""Tag storeys, mixed-use and (fallback) unit count from DevelopmentDescription text.

Regex runs first and is free. Only rows regex can't tag are sent to an LLM,
and only if OPENAI_API_KEY is set — see "Do we need an LLM API?" in
planning-predictor-plan.md. Both paths produce the same columns, so prep.py
doesn't care which one filled a given row.
"""

from __future__ import annotations

import json
import os
import re

import pandas as pd

_WORD_NUMBERS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20,
}
_WORD_PATTERN = "|".join(_WORD_NUMBERS)

STOREY_RE = re.compile(
    rf"(\d{{1,2}}|{_WORD_PATTERN})[\s-]*(?:storey|story|stories|storeys)",
    re.IGNORECASE,
)

MIXED_USE_RE = re.compile(
    r"ground[\s-]*floor\s*(retail|commercial|café|cafe|shop)"
    r"|mixed[\s-]*use"
    r"|retail unit"
    r"|commercial unit",
    re.IGNORECASE,
)

UNITS_RE = re.compile(
    r"(\d{1,4})\s*(?:no\.?\s*)?"
    r"(?:apartments?|residential units?|dwellings?|units?)",
    re.IGNORECASE,
)


def _storey_to_int(raw: str) -> int | None:
    raw = raw.lower()
    if raw in _WORD_NUMBERS:
        return _WORD_NUMBERS[raw]
    try:
        return int(raw)
    except ValueError:
        return None


def extract_storeys(description: str) -> int | None:
    if not isinstance(description, str):
        return None
    match = STOREY_RE.search(description)
    if not match:
        return None
    return _storey_to_int(match.group(1))


def extract_mixed_use(description: str) -> bool:
    if not isinstance(description, str):
        return False
    return bool(MIXED_USE_RE.search(description))


def extract_units(description: str) -> int | None:
    if not isinstance(description, str):
        return None
    match = UNITS_RE.search(description)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def apply_regex_tags(df: pd.DataFrame, description_col: str = "description") -> pd.DataFrame:
    """Adds/overwrites storeys, mixed_use and units_from_text columns in place-ish (returns a copy)."""
    df = df.copy()
    df["storeys"] = df[description_col].apply(extract_storeys)
    df["mixed_use"] = df[description_col].apply(extract_mixed_use)
    df["units_from_text"] = df[description_col].apply(extract_units)
    return df


_LLM_SYSTEM_PROMPT = (
    "You read Irish planning application descriptions. For each one, extract the "
    "number of storeys and whether it includes mixed use (e.g. ground-floor retail "
    "or commercial space alongside residential). If a detail is not stated, use null. "
    "Never guess a number that isn't in the text."
)

_LLM_SCHEMA = {
    "name": "tag_description",
    "schema": {
        "type": "object",
        "properties": {
            "storeys": {"type": ["integer", "null"]},
            "mixed_use": {"type": "boolean"},
        },
        "required": ["storeys", "mixed_use"],
        "additionalProperties": False,
    },
}


def tag_with_llm(descriptions: list[str], model: str = "gpt-4o-mini") -> list[dict]:
    """Tags a batch of descriptions with an OpenAI model. Caller filters to rows
    regex already missed, to keep this small. Returns one dict per description,
    same order, with keys storeys/mixed_use. Raises on API error — caller should
    catch and fall back to "leave it null" rather than block the whole pipeline.
    """
    from openai import OpenAI

    client = OpenAI()
    results = []
    for description in descriptions:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _LLM_SYSTEM_PROMPT},
                {"role": "user", "content": description[:2000]},
            ],
            response_format={"type": "json_schema", "json_schema": {**_LLM_SCHEMA, "strict": True}},
        )
        content = response.choices[0].message.content or "{}"
        results.append(json.loads(content))
    return results


def apply_llm_fallback(df: pd.DataFrame, description_col: str = "description") -> pd.DataFrame:
    """Sends only rows with storeys still null to the LLM. No-ops (and says so)
    if OPENAI_API_KEY isn't set — the regex pass alone is enough to keep building.
    """
    if not os.environ.get("OPENAI_API_KEY"):
        print("[tag_descriptions] OPENAI_API_KEY not set — skipping LLM fallback, regex tags only.")
        return df

    df = df.copy()
    missing = df[df["storeys"].isna()]
    if missing.empty:
        return df

    print(f"[tag_descriptions] sending {len(missing)} rows with no regex storey match to the LLM...")
    try:
        tagged = tag_with_llm(missing[description_col].tolist())
    except Exception as exc:  # noqa: BLE001 - a flaky API must never kill the pipeline
        print(f"[tag_descriptions] LLM fallback failed ({exc}); keeping regex-only tags.")
        return df

    for idx, result in zip(missing.index, tagged):
        if result.get("storeys") is not None:
            df.at[idx, "storeys"] = result["storeys"]
        if result.get("mixed_use"):
            df.at[idx, "mixed_use"] = True
    return df
