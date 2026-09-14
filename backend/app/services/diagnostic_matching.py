"""Which stored findings a new analysis still contains.

Both storages reconcile every analysis against the findings already on record
for the session. A finding still present is carried forward, one that has gone
is resolved, and one never seen before is newly detected. Those three outcomes
become the diagnostic_resolved and code_diagnostic_detected events, time to
fix, and repeat counts - and through them mastery and Study Guider's struggle
triggers. So the matching lives here, once, where it can be tested without a
database, instead of twice inside two storage classes.

A finding is matched by its diagnostic id first. Failing that, by its error
type together with the hash of its flagged line. The second pass is for
records written while ids still included the line number: their ids are ones
no analysis will produce again, and without it the first analysis after ids
changed would record every open finding as fixed and then found again.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Optional

Document = dict[str, Any]


@dataclass
class DiagnosticMatch:
    # (stored record, incoming record) for a finding still present.
    carried: list[tuple[Document, Document]] = field(default_factory=list)
    # Stored records whose finding is gone.
    resolved: list[Document] = field(default_factory=list)
    # Incoming records with nothing on record.
    new: list[Document] = field(default_factory=list)


def match_diagnostics(
    active_documents: Iterable[Document],
    incoming_documents: Iterable[Document],
) -> DiagnosticMatch:
    match = DiagnosticMatch()
    unclaimed = list(active_documents)

    def claim(is_same: Callable[[Document], bool]) -> Optional[Document]:
        for index, document in enumerate(unclaimed):
            if is_same(document):
                return unclaimed.pop(index)
        return None

    # By id, for every incoming finding, before any fallback - so a record
    # that matches exactly is never taken by a looser match first.
    waiting: list[Document] = []
    for incoming in incoming_documents:
        stored = claim(lambda document: document.get("diagnosticId") == incoming.get("diagnosticId"))
        if stored is None:
            waiting.append(incoming)
        else:
            match.carried.append((stored, incoming))

    for incoming in waiting:
        context_hash = incoming.get("codeContextHash")
        stored = (
            claim(
                lambda document: document.get("errorType") == incoming.get("errorType")
                and document.get("codeContextHash") == context_hash
            )
            if context_hash
            else None
        )
        if stored is None:
            match.new.append(incoming)
        else:
            match.carried.append((stored, incoming))

    match.resolved = unclaimed
    return match
