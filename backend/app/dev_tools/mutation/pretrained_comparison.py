"""Offline comparison: hand-built site features against a pretrained code
model's representation of the same site.

The deployed detectors describe each candidate with a few dozen numbers chosen
for that mistake (logic_candidates.py, promoted_candidates.py). The question a
reviewer asks is whether a pretrained model of code - CodeBERT, trained on
millions of functions - would do better if it simply read the code. This
answers it on the same rows, the same split and the same threshold rule:

  * each candidate's program is given to the model with the site marked by two
    comments, /*>>*/ ... /*<<*/, and the model is left frozen;
  * the site is represented by its tokens' mean hidden state together with the
    whole program's, and a logistic regression is trained on that;
  * a third variant joins the pretrained vector to the hand-built features.

Train + validation are fitted, the threshold is chosen out-of-fold with the
same GroupKFold-by-method and precision rule as train_logic_models.py, and the
held-out test split is scored once.

Not part of the service: the server does not load these models (the size of
the instance rules it out), so this runs offline, in its own environment:

    python -m venv research-venv
    research-venv/Scripts/pip install torch --index-url https://download.pytorch.org/whl/cpu
    research-venv/Scripts/pip install transformers==4.46.3 scikit-learn pandas joblib
    research-venv/Scripts/python -m app.dev_tools.mutation.pretrained_comparison   (from backend/)

OUTPUT  backend/models/pretrained_comparison_v1.json and .csv
        data/ml/mutation/_work/embeddings/<model>/<type>.npy   (cache, not kept)
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from typing import Dict, List

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.dev_tools.mutation.java_runner import PROJECT_ROOT, WORK_ROOT
from app.dev_tools.mutation.train_logic_models import CAND_DIR, META, _metrics, choose_threshold, out_of_fold

MODELS_DIR = PROJECT_ROOT / "backend" / "models"
SOURCES_PATH = WORK_ROOT / "sources_v1.jsonl"
MAX_TOKENS = 512
OPEN, CLOSE = "/*>>*/", "/*<<*/"


def _marked(source: str, start: int, end: int) -> tuple[str, int, int]:
    """The source with the site wrapped in markers; char offsets of the site."""
    raw = source.encode("utf-8")
    before = raw[:start].decode("utf-8", errors="replace")
    site = raw[start:end].decode("utf-8", errors="replace")
    after = raw[end:].decode("utf-8", errors="replace")
    text = f"{before}{OPEN}{site}{CLOSE}{after}"
    return text, len(before), len(before) + len(OPEN) + len(site) + len(CLOSE)


class Embedder:
    def __init__(self, name: str, threads: int):
        import torch
        from transformers import AutoModel, AutoTokenizer

        torch.set_num_threads(threads)
        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(name)
        self.model = AutoModel.from_pretrained(name).eval()

    def __call__(self, items: List[tuple[str, int, int]], batch: int = 16) -> np.ndarray:
        vectors = []
        for i in range(0, len(items), batch):
            chunk = items[i:i + batch]
            texts = [self._window(text, a, b) for text, a, b in chunk]
            encoded = self.tokenizer([t for t, _, _ in texts], return_offsets_mapping=True, truncation=True,
                                     max_length=MAX_TOKENS, padding=True, return_tensors="pt")
            offsets = encoded.pop("offset_mapping").numpy()
            with self.torch.no_grad():
                hidden = self.model(**encoded).last_hidden_state.numpy()
            mask = encoded["attention_mask"].numpy().astype(bool)
            for row, (_, a, b) in enumerate(texts):
                tokens = mask[row]
                site = tokens & (offsets[row][:, 1] > a) & (offsets[row][:, 0] < b)
                if not site.any():
                    site = tokens
                vectors.append(np.concatenate([hidden[row][site].mean(axis=0), hidden[row][tokens].mean(axis=0)]))
        return np.vstack(vectors).astype(np.float32)

    def _window(self, text: str, a: int, b: int) -> tuple[str, int, int]:
        # Long programs are cut to a window around the site, so the site is
        # never the part truncation throws away.
        if len(text) <= 1800:
            return text, a, b
        start = max(0, a - 900)
        window = text[start:start + 1800]
        return window, a - start, min(len(window), b - start)


def _previous_extras(path) -> dict:
    """Benchmark figures from an earlier run, kept when the results are rewritten."""
    if not path.exists():
        return {}
    stored = json.loads(path.read_text(encoding="utf-8"))
    return {k: v for k, v in stored.items() if k not in ("model", "results")}


def _pipeline() -> Pipeline:
    return Pipeline([("scaler", StandardScaler()), ("model", LogisticRegression(max_iter=3000, class_weight="balanced", C=0.05))])


def _evaluate(name: str, x_fit: np.ndarray, y_fit: np.ndarray, groups: np.ndarray, x_test: np.ndarray, y_test: np.ndarray) -> dict:
    fit_frame, test_frame = pd.DataFrame(x_fit), pd.DataFrame(x_test)
    oof = out_of_fold(_pipeline, fit_frame, y_fit, groups)
    threshold, reached = choose_threshold(oof, y_fit)
    model = _pipeline().fit(fit_frame, y_fit)
    scores = model.predict_proba(test_frame)[:, 1]
    return {"variant": name, "threshold": round(float(threshold), 4), "threshold_rule": reached,
            "oof": _metrics(y_fit, oof >= threshold, oof), "test": _metrics(y_test, scores >= threshold, scores)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Hand-built features vs a pretrained code model, offline.")
    parser.add_argument("--model", default="microsoft/codebert-base")
    parser.add_argument("--types", default="")
    parser.add_argument("--threads", type=int, default=8)
    parser.add_argument("--benchmark", type=int, default=0,
                        help="time this many sites through the pretrained model, one at a time, and record ms per site")
    args = parser.parse_args()

    sources: Dict[str, str] = {}
    for line in SOURCES_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            sources[item["unit"]] = item["source"]
    calibration = json.loads((MODELS_DIR / "logic_calibration_v1.json").read_text(encoding="utf-8"))["results"]
    types = [t for t in args.types.split(",") if t] or sorted(p.stem.removesuffix("_v1") for p in CAND_DIR.glob("*_v1.csv"))
    cache_dir = WORK_ROOT / "embeddings" / args.model.replace("/", "__")
    cache_dir.mkdir(parents=True, exist_ok=True)
    embedder = None
    results = {}
    out_path = MODELS_DIR / "pretrained_comparison_v1.json"
    if out_path.exists():
        results = json.loads(out_path.read_text(encoding="utf-8")).get("results", {})

    for error_type in types:
        frame = pd.read_csv(CAND_DIR / f"{error_type}_v1.csv")
        frame = frame[frame["unit"].isin(sources)].reset_index(drop=True)
        if frame["label"].nunique() < 2 or (frame["split"] == "test").sum() == 0:
            print(f"{error_type}: skipped (one class or no test rows)")
            continue
        # Cached per site (unit + span), so a rebuilt corpus only embeds the
        # sites it did not have before.
        keys = [f"{u}|{int(s)}|{int(e)}" for u, s, e in zip(frame["unit"], frame["span_start"], frame["span_end"])]
        cache = cache_dir / f"{error_type}.npz"
        known: Dict[str, np.ndarray] = {}
        if cache.exists():
            stored = np.load(cache)
            known = dict(zip(stored["keys"].tolist(), stored["vectors"]))
        elif (cache_dir / f"{error_type}.npy").exists() and len(np.load(cache_dir / f"{error_type}.npy")) == len(frame):
            known = dict(zip(keys, np.load(cache_dir / f"{error_type}.npy")))
        missing = [i for i, key in enumerate(keys) if key not in known]
        if missing:
            if embedder is None:
                embedder = Embedder(args.model, args.threads)
            started = time.perf_counter()
            fresh = embedder([_marked(sources[frame["unit"][i]], int(frame["span_start"][i]), int(frame["span_end"][i])) for i in missing])
            known.update({keys[i]: vector for i, vector in zip(missing, fresh)})
            np.savez(cache, keys=np.array(list(known)), vectors=np.vstack(list(known.values())))
            print(f"{error_type}: embedded {len(missing)} new sites in {time.perf_counter() - started:.0f}s "
                  f"({(time.perf_counter() - started) * 1000 / len(missing):.0f} ms per site)")
        vectors = np.vstack([known[key] for key in keys])

        features = [c for c in frame.columns if c not in META]
        fit, test = (frame["split"] != "test").to_numpy(), (frame["split"] == "test").to_numpy()
        y, groups = frame["label"].to_numpy(), frame["group"].to_numpy()
        hand = frame[features].to_numpy(dtype=np.float32)
        record = {
            "error_type": error_type, "rows": int(len(frame)), "test_rows": int(test.sum()), "test_positives": int(y[test].sum()),
            "hand_features_model": calibration.get(error_type, {}).get("test", {}).get("model"),
            "variants": [
                _evaluate("pretrained", vectors[fit], y[fit], groups[fit], vectors[test], y[test]),
                _evaluate("pretrained+features", np.hstack([vectors, hand])[fit], y[fit], groups[fit], np.hstack([vectors, hand])[test], y[test]),
            ],
        }
        results[error_type] = record
        best = record["variants"][0]["test"]
        hand_model = record["hand_features_model"] or {}
        print(f"{error_type}: features F1={hand_model.get('f1')} AP={hand_model.get('average_precision')} | "
              f"{args.model.split('/')[-1]} F1={best['f1']} AP={best.get('average_precision')} | "
              f"both F1={record['variants'][1]['test']['f1']}")
        out_path.write_text(json.dumps({**_previous_extras(out_path), "model": args.model, "results": results}, indent=2), encoding="utf-8")

    if args.benchmark:
        # One site at a time, as the service would see them: the honest cost
        # of reading a site with the pretrained model on this CPU.
        if embedder is None:
            embedder = Embedder(args.model, args.threads)
        sample = []
        for unit, source in list(sources.items())[: args.benchmark]:
            sample.append(_marked(source, 0, min(len(source.encode("utf-8")), 80)))
        embedder(sample[:2], batch=1)  # warm up
        started = time.perf_counter()
        embedder(sample, batch=1)
        ms = (time.perf_counter() - started) * 1000 / len(sample)
        extras = {"ms_per_site": round(ms, 1), "benchmark_sites": len(sample), "benchmark_threads": args.threads}
        out_path.write_text(json.dumps({**_previous_extras(out_path), **extras, "model": args.model, "results": results}, indent=2), encoding="utf-8")
        print(f"benchmark: {ms:.1f} ms per site ({len(sample)} sites, {args.threads} threads)")

    with (MODELS_DIR / "pretrained_comparison_v1.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["error_type", "test_rows", "test_positives",
                         "features_precision", "features_recall", "features_f1", "features_ap",
                         "pretrained_precision", "pretrained_recall", "pretrained_f1", "pretrained_ap",
                         "both_precision", "both_recall", "both_f1", "both_ap"])
        for error_type, record in sorted(results.items()):
            h = record.get("hand_features_model") or {}
            p, b = record["variants"][0]["test"], record["variants"][1]["test"]
            writer.writerow([error_type, record["test_rows"], record["test_positives"],
                             h.get("precision"), h.get("recall"), h.get("f1"), h.get("average_precision"),
                             p["precision"], p["recall"], p["f1"], p.get("average_precision"),
                             b["precision"], b["recall"], b["f1"], b.get("average_precision")])


if __name__ == "__main__":
    main()
