"""Real students' files in the training pipeline: labelled, indexed, held out.

Everything here works on temporary folders - no database, and nothing written
into data/ml.
"""

from __future__ import annotations

import csv
import math

from app.dev_tools import build_snippet_index, import_labelled_snippets, split_dataset
from app.dev_tools.label_agreement import cohen_kappa, compare

LABELS = split_dataset.TARGET_COLUMNS


def test_kappa_is_one_for_perfect_agreement_and_zero_for_chance():
    assert cohen_kappa([1, 0, 1, 0], [1, 0, 1, 0]) == 1.0
    # Agreement no better than the raters' own label rates predict.
    assert math.isclose(cohen_kappa([1, 1, 0, 0], [1, 0, 1, 0]), 0.0)


def test_disagreements_are_listed_per_file_and_label():
    def row(i, off):
        return {"snippet_id": i, **{c: "0" for c in LABELS}, "has_off_by_one": off}

    a = {"s1": row("s1", "1"), "s2": row("s2", "0")}
    b = {"s1": row("s1", "1"), "s2": row("s2", "1")}

    report, disagreements = compare(a, b)

    assert disagreements == [("s2", "has_off_by_one", "0", "1")]
    assert next(r for r in report if r["label"] == "has_off_by_one")["agreement"] == 0.5


def _unit(snippet_id, source_type, group="", **flags):
    return {
        "snippet_id": snippet_id,
        "source_type": source_type,
        "pair_group": group,
        "primary_label": "NO_ISSUE",
        **{c: str(flags.get(c, 0)) for c in LABELS},
    }


def test_real_files_are_test_only_by_default_and_kept_together_per_student():
    rows = [_unit(f"g{i}", "synthetic_generated", has_off_by_one=i % 2) for i in range(40)]
    rows += [_unit(f"r{i}", "real_student", group="p_ana") for i in range(3)]
    rows += [_unit(f"b{i}", "real_student", group="p_ben") for i in range(3)]
    units = split_dataset._build_units(rows)

    train, val, test = split_dataset._split_units_stratified(units)
    assert {r["snippet_id"] for r in test} >= {"r0", "r1", "r2", "b0", "b1", "b2"}
    assert not any(r["source_type"] == "real_student" for r in train + val)

    train, val, test = split_dataset._split_units_stratified(units, train_on_real=True)
    for student in ("p_ana", "p_ben"):
        homes = [
            name
            for name, split in (("train", train), ("val", val), ("test", test))
            if any(r["pair_group"] == student for r in split)
        ]
        assert len(homes) == 1, f"{student} split across {homes}"


def test_imported_labels_reach_the_snippet_index(tmp_path, monkeypatch):
    export = tmp_path / "export"
    (export / "snippets").mkdir(parents=True)
    (export / "snippets" / "snap_1.java").write_text("class A {}", encoding="utf-8")
    (export / "snippets" / "snap_2.java").write_text("class B {}", encoding="utf-8")

    agreed = tmp_path / "agreed.csv"
    with agreed.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["snippet_id", "participant", *LABELS, "rater", "notes"])
        writer.writeheader()
        writer.writerow({"snippet_id": "snap_1", "participant": "p_ana", **{c: "0" for c in LABELS},
                         "has_incorrect_conditional": "1"})
        writer.writerow({"snippet_id": "snap_2", "participant": "p_ana", **{c: "" for c in LABELS}})

    real_dir = tmp_path / "raw_snippets_real"
    monkeypatch.setattr(import_labelled_snippets, "REAL_DIR", real_dir)
    monkeypatch.setattr(import_labelled_snippets, "LABELS_FILE", real_dir / "labels.csv")
    monkeypatch.setattr(build_snippet_index, "REAL_LABELS_FILE", real_dir / "labels.csv")

    assert import_labelled_snippets.main(["--export", str(export), "--labels", str(agreed)]) == 0

    # The unlabelled row is skipped, never guessed.
    assert (real_dir / "snap_1.java").exists() and not (real_dir / "snap_2.java").exists()

    [row] = build_snippet_index._collect_real_rows()
    assert row["source_type"] == "real_student"
    assert row["pair_group"] == "p_ana"
    assert row["primary_label"] == "INCORRECT_CONDITIONAL_OPERATOR"
    assert row["has_incorrect_conditional"] == "1" and row["is_clean"] == "0"
    assert list(row) == build_snippet_index.FIELDNAMES


def test_without_real_files_the_index_is_unchanged(monkeypatch, tmp_path):
    monkeypatch.setattr(build_snippet_index, "REAL_LABELS_FILE", tmp_path / "missing.csv")
    assert build_snippet_index._collect_real_rows() == []
