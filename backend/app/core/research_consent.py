"""What a student is asked before the code Code Coach checks is kept for research.

================================ A DRAFT ================================
This wording has NOT been through an ethics review. Before any real
participant sees it, replace it with - or check it line by line against - the
wording in the approved ethics application, and change the version.

The version is stored with every decision. A statement that changes after
someone agreed is different terms, so the Account page asks them again and
collection stops counting the old agreement - consent is never stretched over
terms nobody was shown.

Agreeing is not enough on its own: nothing is saved until the deployment turns
on RESEARCH_COLLECTION_ENABLED, which should happen only once ethics approval
is in hand. See app/services/research_collection.py.
=========================================================================
"""

from __future__ import annotations

RESEARCH_CONSENT_VERSION = "code-coach-2026-09-draft-1"

CONSENT_DECISIONS = ("GRANTED", "DECLINED")

RESEARCH_CONSENT_STATEMENT = {
    "title": "Can the code Code Coach checks help improve it?",
    "summary": (
        "Code Coach finds common mistakes in Java using a model trained on example code. "
        "Real student code is the only way to measure how well it works for students, and to "
        "train it better. With your agreement, the Java files Code Coach checks for you can be "
        "kept for that research."
    ),
    "recorded": [
        "The Java file Code Coach checked, each time it changes",
        "What Code Coach found in it, and whether you reported a finding as wrong",
    ],
    "protections": [
        "Your name, email address and account id are replaced by a random code",
        "Only files Code Coach checks are kept - nothing else from your computer",
        "Used only to test and train Code Coach, and seen only by the research team",
        "If you signed your name or email in a comment, remove it - or it is removed before anyone reads the file",
    ],
    "voluntary": (
        "Code Coach works exactly the same whichever you choose. You can change your mind here at "
        "any time, and withdrawing deletes every file already kept from you."
    ),
}
