"""Copy the free course's worked examples into Code Coach, for "Similar example".

The course units live in Study Guider (backend/data/course/<ERROR_TYPE>.json).
Code Coach must not read a sibling repository at run time, so this copies the
before-and-after pairs out of them - every `compare` block - into
knowledge_base/worked_examples.json, with an embedding of each mistake when an
OpenAI key is given, so the editor can show the example closest to the
student's own code.

Embeddings are cut to 256 dimensions (text-embedding-3-small supports that
directly), which keeps the file small and the comparison cheap; the student's
snippet is embedded with the same settings at request time.

USAGE (from backend/)
    python -m app.dev_tools.export_worked_examples \
        --course-dir ../../Study-Guider/backend/data/course \
        --env-file ../../Study-Guider/backend/.env
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import httpx

from app.analysis.error_catalog import ERROR_CATALOG
from app.dev_tools.mutation.generate_base_programs import _load_env_file

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT_PATH = PROJECT_ROOT / "knowledge_base" / "worked_examples.json"
DIMENSIONS = 256


def examples_from(unit: dict) -> list[dict]:
    found = []
    for section in unit.get("sections", []):
        for block in section.get("blocks", []):
            if block.get("type") != "compare":
                continue
            bad, good = block.get("bad") or {}, block.get("good") or {}
            if not bad.get("code") or not good.get("code"):
                continue
            found.append({
                "title": bad.get("title") or section.get("title") or unit.get("title", ""),
                "buggy": bad["code"],
                "fixed": good["code"],
                "note": block.get("note", ""),
                "section": section.get("title", ""),
            })
    return found


def embed(texts: list[str], api_key: str) -> list[list[float]]:
    response = httpx.post(
        "https://api.openai.com/v1/embeddings",
        json={"model": "text-embedding-3-small", "input": texts, "dimensions": DIMENSIONS},
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=120,
    )
    response.raise_for_status()
    data = sorted(response.json()["data"], key=lambda item: item["index"])
    return [[round(x, 5) for x in item["embedding"]] for item in data]


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the course's worked examples.")
    parser.add_argument("--course-dir", required=True)
    parser.add_argument("--env-file", help="a .env holding OPENAI_API_KEY (read, never printed)")
    args = parser.parse_args()
    _load_env_file(args.env_file)
    api_key = os.environ.get("OPENAI_API_KEY")

    library: dict[str, list[dict]] = {}
    for error_type in ERROR_CATALOG:
        path = Path(args.course_dir) / f"{error_type}.json"
        if not path.exists():
            continue
        unit = json.loads(path.read_text(encoding="utf-8"))
        if unit.get("status") != "published":
            continue
        library[error_type] = examples_from(unit)

    if api_key:
        flat = [(error_type, example) for error_type, items in library.items() for example in items]
        for start in range(0, len(flat), 64):
            chunk = flat[start:start + 64]
            vectors = embed([example["buggy"] for _, example in chunk], api_key)
            for (_, example), vector in zip(chunk, vectors):
                example["embedding"] = vector

    OUT_PATH.write_text(json.dumps(library, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    total = sum(len(items) for items in library.values())
    print(f"{total} worked examples for {len(library)} error types -> {OUT_PATH.relative_to(PROJECT_ROOT)}"
          f"{' (with embeddings)' if api_key else ''}")


if __name__ == "__main__":
    main()
