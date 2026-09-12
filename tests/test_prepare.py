"""Pruebas de la preparación del dataset (fase 1) con revisiones pequeñas propias."""

import gzip
import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from bouncer import prepare

REVISION_DEFAULTS = {
    "time_grade": "reqlog",
    "uncertainty_seconds": 1,
    "seq": 1,
    "body": "texto",
    "request_action": "form_edit",
    "related_event_id": None,
}

# Nombre, hora, página y cuerpo elegidos para cubrir cada caso del plan.
REVISIONS = [
    {"rev_id": "w~Z@1", "label": "AgentC", "time": "2026-06-01T09:00:00Z", "page_key": "w~Z"},
    {"rev_id": "w~B@1", "label": "AgentA", "time": "2026-06-01T09:00:00Z", "page_key": "w~B"},
    {"rev_id": "w~P@1", "label": "AgentA", "time": "2026-06-01T10:00:00Z", "page_key": "w~P"},
    {"rev_id": "w~H@1", "label": "[Admin1]", "time": "2026-06-01T10:00:30Z", "page_key": "w~H"},
    {"rev_id": "w~N@1", "label": "", "time": "2026-06-01T10:00:40Z", "page_key": "w~N"},
    {"rev_id": "w~P@2", "label": "AgentA", "time": "2026-06-01T10:01:00Z", "page_key": "w~P", "seq": 2, "body": ""},
    {"rev_id": "w~Q@1", "label": "AgentB", "time": "2026-06-01T10:02:00Z", "page_key": "w~Q", "request_action": None},
    {"rev_id": "w~T@1", "label": "AgentB", "time": "not-a-date", "page_key": "w~T"},
    {"rev_id": "w~M@1", "label": "AgentB", "time": "2026-06-01T10:03:00Z", "page_key": None},
    {"rev_id": "w~R@1", "label": "AgentB", "time": "2026-06-01T10:04:00Z", "page_key": "w~R", "request_action": ""},
    # Tres motivos a la vez: cuenta una sola vez, por el primero del orden.
    {"rev_id": "w~X@1", "label": "[Admin1]", "time": "not-a-date", "page_key": None},
]

LABELS = [
    {"label": "AgentA", "is_human_handle": False},
    {"label": "AgentB", "is_human_handle": False},
    {"label": "AgentC", "is_human_handle": False},
    {"label": "[Admin1]", "is_human_handle": True},
    {"label": "", "is_human_handle": False},
]

USED_IN_ORDER = ["w~B@1", "w~Z@1", "w~P@1", "w~P@2", "w~Q@1", "w~R@1"]


def write_jsonl_gz(path: Path, rows: list[dict]) -> None:
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def corpus(tmp_path: Path) -> Path:
    input_dir = tmp_path / "collusion-wiki"
    input_dir.mkdir()
    write_jsonl_gz(input_dir / "revisions.jsonl.gz", [REVISION_DEFAULTS | r for r in REVISIONS])
    write_jsonl_gz(input_dir / "labels.jsonl.gz", LABELS)
    return input_dir


@pytest.fixture
def prepared(corpus: Path, tmp_path: Path) -> Path:
    output_dir = tmp_path / "prepared"
    prepare.main(["--input-dir", str(corpus), "--output-dir", str(output_dir)])
    return output_dir


def read_events(output_dir: Path) -> list[dict]:
    lines = (output_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines]


def read_cleaning(output_dir: Path) -> dict:
    return json.loads((output_dir / "cleaning.json").read_text(encoding="utf-8"))


def test_corpus_accounting(prepared: Path) -> None:
    cleaning = read_cleaning(prepared)
    events = read_events(prepared)

    assert cleaning["input"]["rows"] == len(REVISIONS)
    assert cleaning["excluded"] == {
        "human_handle": 2,
        "missing_identity": 1,
        "invalid_time": 1,
        "missing_page": 1,
    }
    assert cleaning["recovered"] == {
        "count": 0,
        "reference_field": "related_event_id",
        "missing_identity_with_reference": 0,
    }
    assert cleaning["labels"]["revision_labels_not_in_file"] == 0
    assert cleaning["used"]["rows"] == len(events) == len(USED_IN_ORDER)
    assert cleaning["used"]["rows"] + sum(cleaning["excluded"].values()) == cleaning["input"]["rows"]
    assert cleaning["used"]["agent_ids"] == 3
    assert cleaning["used"]["empty_bodies"] == 1
    assert cleaning["used"]["missing_request_action"] == 2


def test_provenance_and_empty_bodies(prepared: Path) -> None:
    events = {e["rev_id"]: e for e in read_events(prepared)}

    assert events["w~P@2"]["body"] == ""
    for rev_id, event in events.items():
        assert event["operation"] == "wiki.edit"
        assert event["provenance"]["agent_id"] == "label"
        assert event["provenance"]["operation"] == "adapted"
        assert event["time_grade"] == "reqlog" and event["uncertainty_seconds"] == 1
        line = next(i for i, r in enumerate(REVISIONS, start=1) if r["rev_id"] == rev_id)
        assert event["source_ref"] == f"revisions.jsonl.gz:{line}"


def test_source_ref_requires_one_record_per_line(corpus: Path, tmp_path: Path) -> None:
    path = corpus / "revisions.jsonl.gz"
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        first, rest = fh.read().split("\n", 1)
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        fh.write(first + "\n\n" + rest)

    with pytest.raises(ValueError, match="líneas"):
        prepare.prepare(corpus, tmp_path / "out")


def test_recoverable_rows_are_not_silently_dropped(corpus: Path, tmp_path: Path) -> None:
    rows = [REVISION_DEFAULTS | r for r in REVISIONS]
    rows.append(REVISION_DEFAULTS | {"rev_id": "w~A@1", "label": "", "time": "2026-06-01T11:00:00Z", "page_key": "w~A", "related_event_id": "save:w~A@1"})
    write_jsonl_gz(corpus / "revisions.jsonl.gz", rows)

    with pytest.raises(ValueError, match="recuperación no implementada"):
        prepare.prepare(corpus, tmp_path / "out")


def test_missing_identity(prepared: Path) -> None:
    events = read_events(prepared)
    cleaning = read_cleaning(prepared)

    assert {e["rev_id"] for e in events}.isdisjoint({"w~N@1", "w~H@1", "w~X@1"})
    assert all(e["agent_id"] for e in events)
    assert cleaning["human_handles"] == ["[Admin1]"]


def test_missing_request_action(prepared: Path) -> None:
    events = {e["rev_id"]: e for e in read_events(prepared)}

    for rev_id in ("w~Q@1", "w~R@1"):  # null y cadena vacía en el original
        assert events[rev_id]["request_action"] is None
        assert events[rev_id]["provenance"]["request_action"] == "unknown"
    assert events["w~P@1"]["request_action"] == "form_edit"
    assert events["w~P@1"]["provenance"]["request_action"] == "observed"


def test_repeatable_preparation(corpus: Path, tmp_path: Path) -> None:
    first, second = tmp_path / "one", tmp_path / "two"
    prepare.main(["--input-dir", str(corpus), "--output-dir", str(first)])
    prepare.main(["--input-dir", str(corpus), "--output-dir", str(second)])

    for name in ("events.jsonl", "cleaning.json"):
        assert (first / name).read_bytes() == (second / name).read_bytes()


def test_originals_unchanged(corpus: Path, tmp_path: Path) -> None:
    before = {p.name: sha256(p) for p in corpus.iterdir()}
    prepare.main(["--input-dir", str(corpus), "--output-dir", str(tmp_path / "out")])

    assert {p.name: sha256(p) for p in corpus.iterdir()} == before
    cleaning = read_cleaning(tmp_path / "out")
    assert cleaning["input"]["sha256"] == before["revisions.jsonl.gz"]
    assert cleaning["labels"]["sha256"] == before["labels.jsonl.gz"]


def test_event_fields(prepared: Path) -> None:
    events = read_events(prepared)

    assert [e["rev_id"] for e in events] == USED_IN_ORDER
    for event in events:
        assert list(event) == prepare.COLUMNS
    assert "page_family" not in prepare.COLUMNS
    assert "ip16" not in prepare.COLUMNS


def test_dataframe_contract(prepared: Path) -> None:
    df = pd.read_json(prepared / "events.jsonl", lines=True)

    assert list(df.columns) == prepare.COLUMNS
    assert len(df) == len(USED_IN_ORDER)
    assert df["rev_id"].is_unique
    assert df["body"].notna().all()
    assert (df["body"] == "").sum() == 1
    assert df["agent_id"].nunique() == 3
