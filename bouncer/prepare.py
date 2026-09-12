"""Phase 1: from the wiki originals to a single clean, queryable dataset.

Reads `revisions.jsonl.gz` and `labels.jsonl.gz`, excludes humans and rows without
identity, parseable time, or page, and writes `events.jsonl` (one row per revision
used) and `cleaning.json` (the reconciliation). It does not modify the originals.
"""

import argparse
import gzip
import hashlib
import json
from pathlib import Path

import pandas as pd

REVISIONS_FILE = "revisions.jsonl.gz"
LABELS_FILE = "labels.jsonl.gz"
OPERATION = "wiki.edit"
TIME_FORMAT = "ISO8601"

COLUMNS = [
    "rev_id",
    "source_ref",
    "agent_id",
    "time",
    "time_grade",
    "uncertainty_seconds",
    "page_key",
    "seq",
    "body",
    "request_action",
    "operation",
    "provenance",
]

# A row with several reasons counts only once, in this order.
EXCLUSION_ORDER = ["human_handle", "missing_identity", "invalid_time", "missing_page"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl_gz(path: Path) -> pd.DataFrame:
    frame = pd.read_json(path, lines=True, dtype=False)
    # source_ref numbers lines of the original; read_json skips blank lines without warning.
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        lines = sum(1 for _ in fh)
    if lines != len(frame):
        raise ValueError(f"{path}: {lines} lines and {len(frame)} records; cannot number the source")
    return frame


def human_handles(labels: pd.DataFrame) -> list[str]:
    return sorted(labels.loc[labels["is_human_handle"], "label"])


def exclusion_reason(revisions: pd.DataFrame, parsed_time: pd.Series, humans: list[str]) -> pd.Series:
    conditions = {
        "human_handle": revisions["label"].isin(humans),
        "missing_identity": revisions["label"].fillna("") == "",
        "invalid_time": parsed_time.isna(),
        "missing_page": revisions["page_key"].fillna("") == "",
    }
    reason = pd.Series(None, index=revisions.index, dtype=object)
    for name in EXCLUSION_ORDER:
        reason = reason.where(reason.notna() | ~conditions[name], name)
    return reason


def to_events(used: pd.DataFrame, parsed_time: pd.Series) -> pd.DataFrame:
    request_action = used["request_action"].fillna("")
    events = pd.DataFrame(
        {
            "rev_id": used["rev_id"],
            "source_ref": pd.Series(REVISIONS_FILE + ":" + (used.index + 1).astype(str), index=used.index),
            "agent_id": used["label"],
            "time": used["time"],
            "time_grade": used["time_grade"],
            "uncertainty_seconds": used["uncertainty_seconds"],
            "page_key": used["page_key"],
            "seq": used["seq"],
            "body": used["body"],
            "request_action": used["request_action"].where(request_action != "", None),
            "operation": OPERATION,
            "provenance": [
                {"agent_id": "label", "operation": "adapted", "request_action": "observed" if a else "unknown"}
                for a in request_action
            ],
        }
    )
    # Chronological order with a technical tie-break by rev_id; it does not claim real sub-second order.
    order = events.assign(_t=parsed_time).sort_values(["_t", "rev_id"], kind="stable").index
    return events.loc[order, COLUMNS].reset_index(drop=True)


def write_jsonl(path: Path, frame: pd.DataFrame) -> None:
    # json.dumps rather than DataFrame.to_json: pandas escapes "/" and breaks URL reading.
    records = frame.astype(object).where(frame.notna(), None).to_dict("records")
    with path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def prepare(input_dir: Path, output_dir: Path) -> dict:
    revisions_path, labels_path = input_dir / REVISIONS_FILE, input_dir / LABELS_FILE
    revisions = read_jsonl_gz(revisions_path)
    labels = read_jsonl_gz(labels_path)

    humans = human_handles(labels)
    parsed_time = pd.to_datetime(revisions["time"], errors="coerce", utc=True, format=TIME_FORMAT)
    reason = exclusion_reason(revisions, parsed_time, humans)
    used = revisions[reason.isna()]
    events = to_events(used, parsed_time[used.index])

    # Recovery by explicit reference is not implemented because the corpus has no
    # candidates; if any appeared, fail rather than declare 0 recovered.
    recoverable = int(revisions.loc[reason == "missing_identity", "related_event_id"].notna().sum())
    if recoverable:
        raise ValueError(f"{recoverable} rows without identity carry related_event_id: recovery not implemented")

    cleaning = {
        "input": {"file": REVISIONS_FILE, "rows": len(revisions), "sha256": sha256(revisions_path)},
        "labels": {
            "file": LABELS_FILE,
            "rows": len(labels),
            "sha256": sha256(labels_path),
            "revision_labels_not_in_file": int((~revisions["label"].isin(labels["label"])).sum()),
        },
        "human_handles": humans,
        "exclusion_order": EXCLUSION_ORDER,
        "excluded": {name: int((reason == name).sum()) for name in EXCLUSION_ORDER},
        "recovered": {"count": 0, "reference_field": "related_event_id", "missing_identity_with_reference": recoverable},
        "used": {
            "rows": len(events),
            "agent_ids": int(events["agent_id"].nunique()),
            "empty_bodies": int((events["body"] == "").sum()),
            "missing_request_action": int(events["request_action"].isna().sum()),
        },
        "output": {"file": "events.jsonl", "operation": OPERATION, "columns": COLUMNS},
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_dir / "events.jsonl", events)
    (output_dir / "cleaning.json").write_text(
        json.dumps(cleaning, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return cleaning


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input-dir", type=Path, default=Path("data/collusion-wiki"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/prepared/wiki"))
    args = parser.parse_args(argv)
    cleaning = prepare(args.input_dir, args.output_dir)
    print(json.dumps({"excluded": cleaning["excluded"], "used": cleaning["used"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
