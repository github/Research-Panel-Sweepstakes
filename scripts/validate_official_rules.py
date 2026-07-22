#!/usr/bin/env python3
"""
Agent review gate for Research Panel Sweepstakes Official Rules.

Validates a submitted Official Rules document (PDF, Markdown, or text) against the
CELA-approved canonical template. The premise: Official Rules are fixed legal
boilerplate plus a small set of per-study fields. If a submission keeps all of the
boilerplate intact and only changes the allowed fields, it PASSES without a fresh
CELA review. Any change to the boilerplate, a missing/added section, a missing
"No Purchase Necessary", a prohibited word ("raffle"/"lottery"), or a paid-entry
signal FLAGS the document for human/CELA review.

Usage:
    python scripts/validate_official_rules.py <file> [<file> ...]
    python scripts/validate_official_rules.py --spec templates/rules-spec.json <file>

Exit code 0 => all submitted files PASS. Exit code 1 => at least one FLAG.
Writes a Markdown report to $GITHUB_STEP_SUMMARY when set, and prints it to stdout.
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import re
from pathlib import Path

SPEC_DEFAULT = Path(__file__).resolve().parent.parent / "templates" / "rules-spec.json"


def normalize(text: str) -> str:
    """Lowercase, drop punctuation, collapse whitespace. Tolerant of OCR noise."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokens(text: str) -> list[str]:
    return [t for t in normalize(text).split() if len(t) > 2]


def containment(anchor: str, doc_norm_tokens: set[str], fuzzy_index: dict[str, list[str]] | None = None) -> float:
    """Fraction of the anchor's significant tokens present in the document.

    A token counts as present on an exact match, or (to tolerate PDF text-extraction
    glitches such as 'ti' -> '9', e.g. 'administra9on') on a close fuzzy match against a
    document token of similar length.
    """
    at = tokens(anchor)
    if not at:
        return 1.0
    present = 0
    for t in at:
        if t in doc_norm_tokens:
            present += 1
            continue
        if fuzzy_index is not None:
            candidates = fuzzy_index.get(t[0], [])
            if any(
                abs(len(t) - len(d)) <= 2
                and difflib.SequenceMatcher(None, t, d).ratio() >= 0.8
                for d in candidates
            ):
                present += 1
    return present / len(at)


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in (".md", ".markdown", ".txt"):
        return path.read_text(encoding="utf-8", errors="replace")
    if suffix == ".pdf":
        try:
            import pypdf
        except ImportError:  # pragma: no cover
            raise SystemExit("pypdf is required to read PDF submissions (pip install pypdf)")
        reader = pypdf.PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    raise ValueError(f"Unsupported file type: {path.name} (expected .pdf, .md, or .txt)")


def validate(path: Path, spec: dict) -> dict:
    raw = extract_text(path)
    norm = normalize(raw)
    tok_set = set(norm.split())
    # Index doc tokens by first letter for cheap fuzzy lookup.
    fuzzy_index: dict[str, list[str]] = {}
    for t in tok_set:
        if t:
            fuzzy_index.setdefault(t[0], []).append(t)
    threshold = spec.get("containment_threshold", 0.85)

    violations: list[str] = []
    warnings: list[str] = []
    fields: dict[str, str] = {}

    # 1. Required sections present
    for section in spec["required_sections"]:
        if containment(section, tok_set, fuzzy_index) < 0.9:
            violations.append(f"Missing or altered required section: **{section}**")

    # 2. Boilerplate anchors intact
    for key, anchor in spec["boilerplate_anchors"].items():
        score = containment(anchor, tok_set, fuzzy_index)
        if score < threshold:
            violations.append(
                f"Legal boilerplate not intact (`{key}`, match {score:.0%} < {threshold:.0%}): "
                f'expected "{anchor[:70]}…"'
            )

    # 3. Prohibited phrases (paid-entry signals, "raffle"/"lottery"). Guard against
    #    matching inside the GOOD phrase "no purchase necessary ...".
    for phrase in spec["prohibited_phrases"]:
        pat = r"(?<!no )\b" + re.escape(normalize(phrase)) + r"\b"
        if re.search(pat, norm):
            violations.append(f'Prohibited language present: "{phrase}"')

    # 3b. Critical terms that must appear (catches single-word legal swaps that would
    #     otherwise stay above the fuzzy anchor threshold). Fuzzy per-token so OCR
    #     ligature drops (e.g. "Microsoft" -> "microso") don't cause false flags.
    for term, reason in spec.get("critical_terms", {}).items():
        if containment(term, tok_set, fuzzy_index) < 0.99:
            violations.append(f'Required term missing ("{term}"): {reason}')

    # 4. Allowed field presence / sanity (report; missing => warning)
    for name, cfg in spec["allowed_fields"].items():
        rx = cfg.get("expect_regex")
        if rx:
            m = re.search(rx, raw, re.IGNORECASE)
            if m:
                fields[name] = m.group(0).strip()
            elif cfg.get("required"):
                warnings.append(
                    f"Could not locate expected **{name}** ({cfg['description']}) — verify manually."
                )
        else:
            fields[name] = "(free text — verify manually)"

    passed = not violations
    return {
        "file": path.name,
        "passed": passed,
        "violations": violations,
        "warnings": warnings,
        "fields": fields,
    }


def render_report(results: list[dict], spec: dict) -> str:
    lines: list[str] = ["# Official Rules — Agent Review Gate", ""]
    lines.append(
        f"Canonical template: `{spec['canonical_template']}`  ·  "
        f"boilerplate match threshold: {spec.get('containment_threshold', 0.85):.0%}"
    )
    lines.append("")
    for r in results:
        verdict = "✅ **PASS** — conforms to the pre-cleared template, no CELA review required" if r["passed"] \
            else "🚩 **FLAG** — deviates from the template, route to CELA for review"
        lines.append(f"## {r['file']}")
        lines.append("")
        lines.append(verdict)
        lines.append("")
        if r["violations"]:
            lines.append("**Blocking findings:**")
            for v in r["violations"]:
                lines.append(f"- {v}")
            lines.append("")
        if r["warnings"]:
            lines.append("**Please double-check:**")
            for w in r["warnings"]:
                lines.append(f"- {w}")
            lines.append("")
        if r["fields"]:
            lines.append("**Detected per-study fields:**")
            for k, v in r["fields"].items():
                lines.append(f"- `{k}`: {v}")
            lines.append("")
    if all(r["passed"] for r in results):
        lines.append("---")
        lines.append(
            "All submitted documents conform to the approved template. Because only the "
            "allowed per-study fields changed, no per-study CELA review is required."
        )
    else:
        lines.append("---")
        lines.append(
            "One or more documents deviate from the approved template. A human must review the "
            "flagged items with CELA before publishing. Fix the boilerplate to match the canonical "
            "template, or confirm the deviation is intentional and CELA-approved."
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate Official Rules against the canonical template.")
    ap.add_argument("files", nargs="+", help="Official Rules documents (.pdf/.md/.txt)")
    ap.add_argument("--spec", default=str(SPEC_DEFAULT), help="Path to rules-spec.json")
    args = ap.parse_args(argv)

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    results = [validate(Path(f), spec) for f in args.files]
    report = render_report(results, spec)

    print(report)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(report + "\n")

    return 0 if all(r["passed"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
