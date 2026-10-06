#!/usr/bin/env python3
"""triage_parser.py : light log-parsing engine for `asynchronous-release-telemetry-engine`.

Reads a nested `JSON` feedback export, flattens three channel-specific record
shapes, collapses duplicate reports with a `SHA-256` signature, classifies each
fault, scores it, and writes a flat `CSV` ready for the `Jira Product Discovery`
import wizard.

Authority
---------
* Enums, weights, thresholds, and `CSV` columns: `README.md` Sections 5.3 and 6.
* Matching and extraction rules: `docs/TAXONOMY_EXECUTION_LAYER.md` Section 2.
* Import constraints (the 9-point contract): `docs/JPD_ROUTING_MATRIX.md` Section 5.1.

Design stance
-------------
Nothing structural is skipped silently. A malformed export stops the run with a
clear message and a non-zero exit code. The output file is verified against the
9-point contract twice: in memory before writing, and again after re-reading the
written file.

Exit codes
----------
0  success
1  file could not be read or written
2  the export failed validation (structure, counts, fields, timestamps)
3  the generated output violated the import contract (internal fault)

Dependencies: Python 3.11 or newer, standard library only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if sys.version_info < (3, 11):  # `datetime.fromisoformat` must accept a trailing `Z`
    sys.exit("triage_parser.py requires Python 3.11 or newer.")

# --------------------------------------------------------------------------- #
# Constants: file locations
# --------------------------------------------------------------------------- #
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = REPO_ROOT / "data" / "raw" / "feedback_export_sample.json"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "processed" / "triaged_feedback.csv"

# --------------------------------------------------------------------------- #
# Constants: export contract (`README.md` Section 6.1)
# --------------------------------------------------------------------------- #
SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class ChannelSpec:
    """Location of the four required values inside one channel's record shape."""

    channel: str  # enum value used in the output, for example `SLACK`
    record_id: tuple[str, ...]
    timestamp: tuple[str, ...]
    reporter: tuple[str, ...]
    text: tuple[str, ...]


CHANNEL_SPECS: dict[str, ChannelSpec] = {
    "slack": ChannelSpec("SLACK", ("msg_id",), ("ts",), ("user", "id"), ("payload", "text")),
    "email": ChannelSpec("EMAIL", ("message_id",), ("received_at",), ("from", "address"), ("body", "plain")),
    "support_form": ChannelSpec(
        "SUPPORT_FORM", ("ticket_id",), ("submitted_at",), ("reporter", "ref"), ("fields", "description")
    ),
}

# --------------------------------------------------------------------------- #
# Constants: output contract (`README.md` Section 6.2)
# --------------------------------------------------------------------------- #
COLUMNS: tuple[str, ...] = (
    "dedup_hash",
    "error_signature",
    "source_channels",
    "first_seen_utc",
    "last_seen_utc",
    "occurrence_count",
    "affected_users",
    "root_cause_layer",
    "feature_tier",
    "funds_at_risk",
    "layer_weight",
    "reach_factor",
    "triage_score",
    "priority_band",
    "routing_queue",
    "sample_summary",
)
DISPLAY_LIMIT = 255  # `Short text` and `Summary` limit in `Jira Product Discovery`
HASH_LENGTH = 12
UTC_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
FORMULA_TRIGGERS = ("=", "+", "-", "@")  # leading characters a spreadsheet may execute

# --------------------------------------------------------------------------- #
# Constants: taxonomy (`README.md` Section 5.3) and rule sets (`docs/TAXONOMY_EXECUTION_LAYER.md` Section 2.3)
# --------------------------------------------------------------------------- #
LAYER_WEIGHTS = {
    "SMART_CONTRACT": 5,
    "BACKEND_DB": 5,
    "API_GATEWAY": 3,
    "FRONTEND_UI": 1,
    "UNCLASSIFIED": 2,
}
ROUTING_QUEUES = {
    "SMART_CONTRACT": "Q1_BACKEND_PLATFORM",
    "BACKEND_DB": "Q1_BACKEND_PLATFORM",
    "API_GATEWAY": "Q1_BACKEND_PLATFORM",
    "FRONTEND_UI": "Q2_FRONTEND_EXPERIENCE",
    "UNCLASSIFIED": "Q0_MANUAL_REVIEW",
}
FEATURE_TIERS = ("TIER_1_CORE_LEDGER", "TIER_2_USER_WORKFLOW", "TIER_3_PRESENTATION")
PRIORITY_BANDS = ("P0_CRITICAL", "P1_HIGH", "P2_MEDIUM", "P3_LOW")
BAND_RANK = {band: rank for rank, band in enumerate(PRIORITY_BANDS)}
DEFAULT_TIER = "TIER_2_USER_WORKFLOW"

# Layers are tried in this order; the first layer with a matching phrase wins.
LAYER_PHRASES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("SMART_CONTRACT", ("execution reverted", "revert", "out of gas", "gas estimation", "contract call")),
    (
        "BACKEND_DB",
        (
            "balance not updating", "balance is wrong", "wrong balance", "wrong amount", "stale",
            "out of sync", "missing from history", "history missing", "charged twice",
            "double charged", "deducted twice",
        ),
    ),
    (
        "API_GATEWAY",
        ("bad gateway", "gateway timeout", "service unavailable", "timed out", "timeout", "rate limit", "too many requests"),
    ),
    (
        "FRONTEND_UI",
        (
            "misaligned", "overlap", "typo", "spelling", "wrong color", "wrong colour", "font", "layout",
            "cut off", "dark mode", "truncated", "icon", "alignment",
        ),
    ),
)
# Tiers are tried in this order; no match gives `DEFAULT_TIER`.
TIER_PHRASES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "TIER_3_PRESENTATION",
        ("color", "colour", "font", "layout", "typo", "spelling", "icon", "dark mode", "misaligned", "alignment", "theme"),
    ),
    (
        "TIER_1_CORE_LEDGER",
        (
            "transfer", "transaction", "send", "sent", "withdraw", "deposit", "stake", "staking", "swap",
            "payment", "balance", "funds", "charged",
        ),
    ),
    (
        "TIER_2_USER_WORKFLOW",
        (
            "login", "log in", "sign in", "wallet connect", "connect wallet", "onboarding", "notification",
            "settings", "profile", "password", "verification",
        ),
    ),
)
FUNDS_PHRASES: tuple[str, ...] = (
    "charged twice", "double charged", "deducted twice", "funds missing", "funds lost", "lost my funds",
    "lost my tokens", "tokens disappeared", "money is gone", "never arrived", "funds stuck", "stuck funds",
)


def _compile_phrases(phrases: tuple[str, ...]) -> tuple[tuple[str, re.Pattern[str]], ...]:
    """Pair each phrase with a word-start pattern, so `font` also matches `fonts`."""
    return tuple((p, re.compile(r"\b" + re.escape(p))) for p in phrases)


_LAYER_MATCHERS = tuple((name, _compile_phrases(ph)) for name, ph in LAYER_PHRASES)
_TIER_MATCHERS = tuple((name, _compile_phrases(ph)) for name, ph in TIER_PHRASES)
_FUNDS_MATCHERS = _compile_phrases(FUNDS_PHRASES)

# Normalization steps 2 to 8, applied in this order to lowercase text (Section 2.1).
# Steps 3 and 4 must run while digits are still present, so `NUMBER` stays last.
_VOLATILE_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p)
    for p in (
        r"https?://\S+",  # 2  URL
        r"\b(?:tx|txid|txn|hash)\s*:?\s*0x[0-9a-f]{6,}",  # 3  labelled transaction hash
        r"0x[0-9a-f]{6,}",  # 4  bare hex string
        r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",  # 5  UUID
        r"\b\d{4}-\d{2}-\d{2}(?:[t ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:z|[+-]\d{2}:?\d{2})?)?",  # 6  ISO 8601
        r"\b\d{1,2}:\d{2}(?::\d{2})?\s?(?:am|pm)?\b",  # 7  clock time
        r"\d+(?:[.,]\d+)*",  # 8  number
    )
)
_SENTENCE_SPLIT = re.compile(r"[.!?\n]+")
_NON_SIGNATURE_CHARS = re.compile(r"[^a-z0-9 ]")
_WHITESPACE = re.compile(r"\s+")
_SLACK_TS = re.compile(r"(\d{9,11})(?:\.\d+)?")


# --------------------------------------------------------------------------- #
# Exceptions
# --------------------------------------------------------------------------- #
class ExportValidationError(Exception):
    """The input export is structurally invalid. Maps to exit code 2."""


class OutputContractError(Exception):
    """The generated output violates the import contract. Maps to exit code 3."""


# --------------------------------------------------------------------------- #
# Data structures
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Report:
    """One flattened feedback report."""

    record_id: str
    channel: str
    reporter_key: str  # `CHANNEL:identifier`; identities are not resolved across channels
    timestamp: datetime  # timezone-aware, `UTC`
    text: str


@dataclass(frozen=True)
class TriagedRow:
    """One output row: a group of reports that share a normalized signature."""

    full_signature: str  # un-truncated; the `dedup_hash` is computed from this value
    dedup_hash: str
    error_signature: str  # display value, at most 255 characters
    source_channels: str
    first_seen_utc: str
    last_seen_utc: str
    occurrence_count: int
    affected_users: int
    root_cause_layer: str
    feature_tier: str
    funds_at_risk: str
    layer_weight: int
    reach_factor: int
    triage_score: int
    priority_band: str
    routing_queue: str
    sample_summary: str

    def as_record(self) -> list[str]:
        """Values in `COLUMNS` order, as strings."""
        return [str(getattr(self, column)) for column in COLUMNS]


# --------------------------------------------------------------------------- #
# Stage 1: load and validate the export
# --------------------------------------------------------------------------- #
def load_export(path: Path) -> Any:
    """Read the export as `UTF-8` `JSON`. Raises `OSError` or `ExportValidationError`."""
    with path.open("r", encoding="utf-8") as handle:
        try:
            return json.load(handle)
        except json.JSONDecodeError as exc:
            raise ExportValidationError(f"{path}: not valid JSON ({exc})") from exc


def _is_int(value: Any) -> bool:
    return type(value) is int  # excludes `bool`, which subclasses `int`


def validate_envelope(payload: Any) -> dict[str, list[Any]]:
    """Check `export_meta` against the payload arrays. Fail loudly on any mismatch.

    Returns the three channel arrays keyed by their `JSON` names.
    """
    if not isinstance(payload, dict):
        raise ExportValidationError("top level must be a JSON object")
    for key in ("export_meta", "channels"):
        if not isinstance(payload.get(key), dict):
            raise ExportValidationError(f"missing or invalid top-level object '{key}'")
    meta, channels = payload["export_meta"], payload["channels"]

    if meta.get("schema_version") != SCHEMA_VERSION:
        raise ExportValidationError(
            f"export_meta.schema_version must be '{SCHEMA_VERSION}', found {meta.get('schema_version')!r}"
        )
    declared_total = meta.get("total_records")
    if not _is_int(declared_total) or declared_total < 0:
        raise ExportValidationError("export_meta.total_records must be a non-negative integer")
    declared_counts = meta.get("channel_counts")
    if not isinstance(declared_counts, dict) or set(declared_counts) != set(CHANNEL_SPECS):
        raise ExportValidationError(
            f"export_meta.channel_counts must contain exactly these keys: {sorted(CHANNEL_SPECS)}"
        )
    for name, declared in declared_counts.items():
        if not _is_int(declared) or declared < 0:
            raise ExportValidationError(f"export_meta.channel_counts.{name} must be a non-negative integer")

    unknown = sorted(set(channels) - set(CHANNEL_SPECS))
    if unknown:
        raise ExportValidationError(f"channels contains unsupported keys that would be ignored: {unknown}")
    arrays: dict[str, list[Any]] = {}
    for name in CHANNEL_SPECS:
        if not isinstance(channels.get(name), list):
            raise ExportValidationError(f"channels.{name} must be an array")
        arrays[name] = channels[name]

    mismatches = [
        f"channels.{name}: declared {declared_counts[name]}, found {len(arrays[name])}"
        for name in CHANNEL_SPECS
        if declared_counts[name] != len(arrays[name])
    ]
    actual_total = sum(len(a) for a in arrays.values())
    if declared_total != actual_total:
        mismatches.append(f"total_records: declared {declared_total}, found {actual_total}")
    if sum(declared_counts.values()) != declared_total:
        mismatches.append(
            f"export_meta is internally inconsistent: channel_counts sum to {sum(declared_counts.values())} "
            f"but total_records is {declared_total}"
        )
    if mismatches:
        raise ExportValidationError("record counts do not match the payload: " + "; ".join(mismatches))
    return arrays


def _extract(record: dict[str, Any], path: tuple[str, ...], label: str) -> str:
    current: Any = record
    for step in path:
        if not isinstance(current, dict) or step not in current:
            raise ExportValidationError(f"{label}: missing field '{'.'.join(path)}'")
        current = current[step]
    if not isinstance(current, str) or not current.strip():
        raise ExportValidationError(f"{label}: field '{'.'.join(path)}' must be a non-empty string")
    return current


def parse_timestamp(channel: str, value: str, label: str) -> datetime:
    """Convert a raw channel timestamp to a timezone-aware `UTC` datetime."""
    if channel == "SLACK":
        match = _SLACK_TS.fullmatch(value)
        if not match:
            raise ExportValidationError(f"{label}: 'ts' must be epoch seconds such as '1789373520.000100', found {value!r}")
        return datetime.fromtimestamp(int(match.group(1)), tz=timezone.utc)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ExportValidationError(f"{label}: timestamp {value!r} is not ISO 8601") from exc
    if parsed.tzinfo is None:
        raise ExportValidationError(f"{label}: timestamp {value!r} has no time zone; refusing to guess")
    return parsed.astimezone(timezone.utc)


def flatten(arrays: dict[str, list[Any]]) -> list[Report]:
    """Map the three channel shapes to unified reports. Collects every error before failing."""
    reports: list[Report] = []
    errors: list[str] = []
    for name, spec in CHANNEL_SPECS.items():
        for index, record in enumerate(arrays[name]):
            label = f"channels.{name}[{index}]"
            if not isinstance(record, dict):
                errors.append(f"{label}: record must be an object")
                continue
            try:
                record_id = _extract(record, spec.record_id, label)
                label = f"{label} ({record_id})"
                raw_ts = _extract(record, spec.timestamp, label)
                reporter = _extract(record, spec.reporter, label)
                text = _extract(record, spec.text, label)
                reports.append(
                    Report(record_id, spec.channel, f"{spec.channel}:{reporter}", parse_timestamp(spec.channel, raw_ts, label), text)
                )
            except ExportValidationError as exc:
                errors.append(str(exc))
    id_counts = Counter(r.record_id for r in reports)
    errors.extend(f"duplicate record id '{rid}' appears {n} times" for rid, n in sorted(id_counts.items()) if n > 1)
    if errors:
        shown = errors[:25]
        extra = f"\n... and {len(errors) - 25} more" if len(errors) > 25 else ""
        raise ExportValidationError(f"{len(errors)} invalid record(s):\n  - " + "\n  - ".join(shown) + extra)
    return reports


# --------------------------------------------------------------------------- #
# Stage 2: normalization and deduplication (Section 2.1 and 2.2)
# --------------------------------------------------------------------------- #
def normalize_signature(text: str) -> str:
    """Return the `error_signature` for one report."""
    working = text.lower()
    for pattern in _VOLATILE_PATTERNS:
        working = pattern.sub(" ", working)
    segments = _SENTENCE_SPLIT.split(working)
    chosen = next(
        (seg for seg in segments if sum(1 for word in seg.split() if re.search(r"[a-z0-9]", word)) >= 3),
        working,
    )
    return _WHITESPACE.sub(" ", _NON_SIGNATURE_CHARS.sub(" ", chosen)).strip()


def make_hash(signature: str) -> str:
    return hashlib.sha256(signature.encode("utf-8")).hexdigest()[:HASH_LENGTH]


def truncate_display(value: str, limit: int = DISPLAY_LIMIT) -> str:
    """Shorten to `limit` characters, ending in `...` when shortened."""
    return value if len(value) <= limit else value[: limit - 3] + "..."


def group_reports(reports: list[Report]) -> dict[str, list[Report]]:
    """Group by the full normalized signature. Refuses reports with no usable signature."""
    groups: dict[str, list[Report]] = {}
    empty: list[str] = []
    for report in reports:
        signature = normalize_signature(report.text)
        if not signature:
            empty.append(report.record_id)
            continue
        groups.setdefault(signature, []).append(report)
    if empty:
        raise ExportValidationError(
            "reports with no usable fault statement after normalization (no ASCII letters or digits "
            f"outside volatile tokens): {', '.join(sorted(empty))}"
        )
    return groups


# --------------------------------------------------------------------------- #
# Stage 3: classification, scoring, routing (Section 2.3 and `README.md` Section 5.3)
# --------------------------------------------------------------------------- #
def _matches_any(signature: str, matchers: tuple[tuple[str, re.Pattern[str]], ...]) -> bool:
    return any(pattern.search(signature) for _, pattern in matchers)


def classify_layer(signature: str) -> str:
    for layer, matchers in _LAYER_MATCHERS:
        if _matches_any(signature, matchers):
            return layer
    return "UNCLASSIFIED"


def classify_tier(signature: str) -> str:
    for tier, matchers in _TIER_MATCHERS:
        if _matches_any(signature, matchers):
            return tier
    return DEFAULT_TIER


def funds_at_risk(signature: str) -> bool:
    return _matches_any(signature, _FUNDS_MATCHERS)


def reach_factor(affected_users: int) -> int:
    for ceiling, factor in ((1, 1), (4, 2), (9, 3), (24, 4)):
        if affected_users <= ceiling:
            return factor
    return 5


def priority_band(score: int, at_risk: bool) -> str:
    if at_risk or score >= 20:
        return "P0_CRITICAL"
    if score >= 10:
        return "P1_HIGH"
    if score >= 4:
        return "P2_MEDIUM"
    return "P3_LOW"


def format_utc(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_summary(report: Report) -> str:
    """Single-line representative text, safe to open in a spreadsheet, at most 255 characters."""
    summary = _WHITESPACE.sub(" ", report.text).strip()
    if summary.startswith(FORMULA_TRIGGERS):
        summary = "'" + summary  # neutralize spreadsheet formula injection
    return truncate_display(summary)


def triage(groups: dict[str, list[Report]]) -> list[TriagedRow]:
    """Turn signature groups into scored, routed, ordered rows."""
    rows: list[TriagedRow] = []
    for signature, members in groups.items():
        ordered = sorted(members, key=lambda r: (r.timestamp, r.record_id))
        layer = classify_layer(signature)
        users = len({r.reporter_key for r in members})
        factor = reach_factor(users)
        score = LAYER_WEIGHTS[layer] * factor
        at_risk = funds_at_risk(signature)
        rows.append(
            TriagedRow(
                full_signature=signature,
                dedup_hash=make_hash(signature),
                error_signature=truncate_display(signature),
                source_channels="|".join(sorted({r.channel for r in members})),
                first_seen_utc=format_utc(ordered[0].timestamp),
                last_seen_utc=format_utc(ordered[-1].timestamp),
                occurrence_count=len(members),
                affected_users=users,
                root_cause_layer=layer,
                feature_tier=classify_tier(signature),
                funds_at_risk="TRUE" if at_risk else "FALSE",
                layer_weight=LAYER_WEIGHTS[layer],
                reach_factor=factor,
                triage_score=score,
                priority_band=priority_band(score, at_risk),
                routing_queue=ROUTING_QUEUES[layer],
                sample_summary=build_summary(ordered[0]),
            )
        )
    rows.sort(key=lambda r: (BAND_RANK[r.priority_band], -r.triage_score, -r.affected_users, r.dedup_hash))
    return rows


# --------------------------------------------------------------------------- #
# Stage 4: output contract (`docs/JPD_ROUTING_MATRIX.md` Section 5.1) and writing
# --------------------------------------------------------------------------- #
def verify_rows(rows: list[TriagedRow]) -> None:
    """Check every row against the 9-point import contract and the scoring rules."""
    problems: list[str] = []
    for row in rows:
        tag = row.dedup_hash
        values = row.as_record()
        # Point 3: every value is single-line
        if any("\n" in v or "\r" in v for v in values):
            problems.append(f"{tag}: a value contains a line break (point 3)")
        # Point 4: summary length
        if len(row.sample_summary) > DISPLAY_LIMIT:
            problems.append(f"{tag}: sample_summary exceeds {DISPLAY_LIMIT} characters (point 4)")
        # Point 5: signature display length, and hash computed on the full text
        if len(row.error_signature) > DISPLAY_LIMIT:
            problems.append(f"{tag}: error_signature exceeds {DISPLAY_LIMIT} characters (point 5)")
        if row.dedup_hash != make_hash(row.full_signature):
            problems.append(f"{tag}: dedup_hash does not match the full signature (point 5)")
        # Point 6: enums
        if row.root_cause_layer not in LAYER_WEIGHTS:
            problems.append(f"{tag}: unknown root_cause_layer {row.root_cause_layer!r} (point 6)")
        if row.feature_tier not in FEATURE_TIERS:
            problems.append(f"{tag}: unknown feature_tier {row.feature_tier!r} (point 6)")
        if row.priority_band not in PRIORITY_BANDS:
            problems.append(f"{tag}: unknown priority_band {row.priority_band!r} (point 6)")
        if row.routing_queue not in set(ROUTING_QUEUES.values()):
            problems.append(f"{tag}: unknown routing_queue {row.routing_queue!r} (point 6)")
        # Point 7: boolean literal
        if row.funds_at_risk not in ("TRUE", "FALSE"):
            problems.append(f"{tag}: funds_at_risk must be TRUE or FALSE (point 7)")
        # Point 8: datetime format
        for column in ("first_seen_utc", "last_seen_utc"):
            if not UTC_PATTERN.match(getattr(row, column)):
                problems.append(f"{tag}: {column} is not ISO 8601 UTC ending in Z (point 8)")
        if row.first_seen_utc > row.last_seen_utc:
            problems.append(f"{tag}: first_seen_utc is later than last_seen_utc")
        # Point 9: pipe-delimited, sorted, unique channels
        parts = row.source_channels.split("|")
        known = {spec.channel for spec in CHANNEL_SPECS.values()}
        if not all(parts) or parts != sorted(set(parts)) or not set(parts) <= known:
            problems.append(f"{tag}: source_channels must be sorted, unique, pipe-delimited known channels (point 9)")
        # Scoring consistency
        if row.affected_users < 1 or row.occurrence_count < row.affected_users:
            problems.append(f"{tag}: inconsistent occurrence_count and affected_users")
        if (
            row.layer_weight != LAYER_WEIGHTS.get(row.root_cause_layer)
            or row.reach_factor != reach_factor(row.affected_users)
            or row.triage_score != row.layer_weight * row.reach_factor
            or row.priority_band != priority_band(row.triage_score, row.funds_at_risk == "TRUE")
            or row.routing_queue != ROUTING_QUEUES.get(row.root_cause_layer)
        ):
            problems.append(f"{tag}: score, band, or routing does not follow the rules")
    if len({r.dedup_hash for r in rows}) != len(rows):
        problems.append("duplicate dedup_hash values across rows")
    if problems:
        raise OutputContractError("output contract violated:\n  - " + "\n  - ".join(problems))


def write_csv(rows: list[TriagedRow], path: Path) -> None:
    """Write `UTF-8` (no byte-order mark), comma-delimited, `LF` line endings, fixed header."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        writer.writerow(COLUMNS)
        writer.writerows(row.as_record() for row in rows)


def verify_written_file(rows: list[TriagedRow], path: Path) -> None:
    """Re-read the written file and confirm it matches the in-memory rows (points 1 to 3)."""
    raw = path.read_bytes()
    problems: list[str] = []
    if raw.startswith(b"\xef\xbb\xbf"):
        problems.append("file starts with a byte-order mark")
    if b"\r" in raw:
        problems.append("file contains carriage returns")
    try:
        text = raw.decode("utf-8")  # point 2: strict `UTF-8`
    except UnicodeDecodeError as exc:
        raise OutputContractError(f"written file is not valid UTF-8: {exc}") from exc
    parsed = list(csv.reader(text.splitlines(), delimiter=","))
    if not parsed or tuple(parsed[0]) != COLUMNS:  # point 1: header identical, same order
        problems.append("header row does not match the 16 contract columns")
    elif parsed[1:] != [row.as_record() for row in rows]:
        problems.append("data rows read back from disk differ from the rows generated in memory")
    if len(text.splitlines()) != len(rows) + 1:
        problems.append("line count differs from rows plus header (a value may span lines)")
    if problems:
        raise OutputContractError("written file failed verification:\n  - " + "\n  - ".join(problems))


# --------------------------------------------------------------------------- #
# Command line
# --------------------------------------------------------------------------- #
def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Flatten, deduplicate, classify, and score a feedback export into a Jira Product Discovery import CSV."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help=f"export file (default: {DEFAULT_INPUT})")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help=f"CSV file to write (default: {DEFAULT_OUTPUT})")
    return parser


def print_summary(arrays: dict[str, list[Any]], reports: list[Report], rows: list[TriagedRow], output: Path) -> None:
    bands = Counter(row.priority_band for row in rows)
    counts = " ".join(f"{name}={len(arrays[name])}" for name in CHANNEL_SPECS)
    print("Validation passed     : schema_version " + SCHEMA_VERSION + f"; total_records {len(reports)} and channel counts ({counts}) match the payload")
    print(f"Records ingested      : {len(reports)}")
    print(f"Unique signatures     : {len(rows)}")
    print(f"Duplicates collapsed  : {len(reports) - len(rows)}")
    print("Band distribution     : " + " ".join(f"{band}={bands[band]}" for band in PRIORITY_BANDS))
    print(f"Manual review queue   : {sum(1 for r in rows if r.routing_queue == 'Q0_MANUAL_REVIEW')}")
    print("Output contract       : 9 of 9 checks passed (in memory and after re-reading the written file)")
    print(f"Rows written          : {len(rows)} -> {output}")


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):  # keep consoles with legacy code pages from crashing
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    args = build_argument_parser().parse_args(argv)
    try:
        payload = load_export(args.input)
        arrays = validate_envelope(payload)
        reports = flatten(arrays)
        rows = triage(group_reports(reports))
        verify_rows(rows)
        write_csv(rows, args.output)
        verify_written_file(rows, args.output)
    except ExportValidationError as exc:
        print(f"EXPORT VALIDATION FAILED: {exc}", file=sys.stderr)
        return 2
    except OutputContractError as exc:
        print(f"OUTPUT CONTRACT FAILED: {exc}", file=sys.stderr)
        return 3
    except OSError as exc:
        print(f"FILE ERROR: {exc}", file=sys.stderr)
        return 1
    print_summary(arrays, reports, rows, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
