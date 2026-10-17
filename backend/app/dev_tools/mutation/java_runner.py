"""Compile and run Java for the mutation corpus, in bulk and in parallel.

Two Java helpers live in harness/: BatchCompile (many files, one JVM) and
Fuzz (one class's static methods on seeded random inputs). This module builds
them once and drives them from Python:

    compile_many([(source, out_dir), ...])   -> {source: None | error}
    behaviour_many([(class_dir, name), ...]) -> {(class_dir, name): transcript}

A transcript is the full text Fuzz printed. Two classes behave the same when
their transcripts are equal, because Fuzz feeds both the same inputs.

Needs a JDK (javac and java) on PATH. Nothing here touches a database or the
network.
"""

from __future__ import annotations

import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

HARNESS_DIR = Path(__file__).resolve().parent / "harness"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
WORK_ROOT = PROJECT_ROOT / "data" / "ml" / "mutation" / "_work"
HARNESS_BUILD = WORK_ROOT / "harness"

WORKERS = max(4, min(16, (os.cpu_count() or 4) - 2))
RUN_TIMEOUT_SECONDS = 20


def build_harness() -> Path:
    """Compile Fuzz and BatchCompile, once, into the work folder."""
    HARNESS_BUILD.mkdir(parents=True, exist_ok=True)
    sources = sorted(HARNESS_DIR.glob("*.java"))
    built = [HARNESS_BUILD / (source.stem + ".class") for source in sources]
    newest_source = max(source.stat().st_mtime for source in sources)
    if all(path.exists() and path.stat().st_mtime >= newest_source for path in built):
        return HARNESS_BUILD
    subprocess.run(
        ["javac", "-d", str(HARNESS_BUILD), *map(str, sources)],
        check=True,
        capture_output=True,
    )
    return HARNESS_BUILD


def _compile_chunk(chunk: List[Tuple[Path, Path]]) -> Dict[str, Optional[str]]:
    payload = "".join(f"{source}\t{out}\n" for source, out in chunk)
    process = subprocess.run(
        ["java", "-cp", str(HARNESS_BUILD), "BatchCompile"],
        input=payload,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60 + 2 * len(chunk),
    )
    results: Dict[str, Optional[str]] = {}
    for line in process.stdout.splitlines():
        parts = line.split("\t")
        if parts[0] == "OK":
            results[parts[1]] = None
        elif parts[0] == "ERR":
            results[parts[1]] = parts[2] if len(parts) > 2 else "compile error"
    for source, _ in chunk:
        results.setdefault(str(source), "compiler did not report")
    return results


def compile_many(jobs: Iterable[Tuple[Path, Path]]) -> Dict[str, Optional[str]]:
    """Compile each source into its own folder. None means it compiled."""
    build_harness()
    jobs = list(jobs)
    if not jobs:
        return {}
    size = max(1, -(-len(jobs) // WORKERS))
    chunks = [jobs[i:i + size] for i in range(0, len(jobs), size)]
    results: Dict[str, Optional[str]] = {}
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for part in pool.map(_compile_chunk, chunks):
            results.update(part)
    return results


_INT_LITERAL = re.compile(r"(?<![\w.])\d+(?![\w.])")


def literals(*sources: str) -> str:
    """The small int literals in the source(s), for Fuzz to probe around.

    Both versions of a comparison must see the same inputs, so callers pass
    every source being compared and get one shared list.
    """
    found = []
    for source in sources:
        for match in _INT_LITERAL.findall(source or ""):
            value = int(match)
            if value <= 10_000 and value not in found:
                found.append(value)
    return ",".join(str(v) for v in sorted(found)[:16])


def _behaviour(job: tuple, inputs: int) -> str:
    class_dir, name = job[0], job[1]
    constants = job[2] if len(job) > 2 else ""
    classpath = os.pathsep.join([str(HARNESS_BUILD), str(class_dir)])
    try:
        process = subprocess.run(
            ["java", "-Xss8m", "-XX:+UseSerialGC", "-XX:TieredStopAtLevel=1",
             "-cp", classpath, "Fuzz", name, str(inputs), constants],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=RUN_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return "HARNESS_TIMEOUT"
    if process.returncode != 0 and not process.stdout:
        tail = process.stderr.strip().splitlines()
        return "HARNESS_ERROR " + (tail[-1] if tail else "")
    return process.stdout


def behaviour_many(jobs: Iterable[Tuple[Path, str]], inputs: int = 40) -> Dict[Tuple[Path, str], str]:
    """Run Fuzz on each compiled class. Keyed by the job tuple."""
    build_harness()
    jobs = list(jobs)
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        transcripts = list(pool.map(lambda job: _behaviour(job, inputs), jobs))
    return dict(zip(jobs, transcripts))


def method_transcripts(transcript: str) -> Dict[str, str]:
    """Split one class's transcript into one block per method signature."""
    blocks: Dict[str, List[str]] = {}
    current = None
    for line in transcript.splitlines():
        if line.startswith("  ") and current is not None:
            blocks[current].append(line)
            continue
        head = line.split("#", 1)[0].removeprefix("SKIP ")
        current = head
        blocks.setdefault(current, []).append(line)
    return {name: "\n".join(lines) for name, lines in blocks.items()}
