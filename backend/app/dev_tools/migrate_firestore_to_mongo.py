"""Copy every collection from Firestore into MongoDB.

    python -m app.dev_tools.migrate_firestore_to_mongo            # dry run
    python -m app.dev_tools.migrate_firestore_to_mongo --apply    # writes

Run this ONCE, while both stores are still reachable, before switching
build_storage() over by unsetting the FIREBASE_* variables.

Dry run by default: this reads a live database and writes to another one, and
the counts it reports are the thing worth checking before either happens.

============================ WHY THIS EXISTS ============================
Firestore was the only cross-cloud dependency in a platform deploying to AWS,
and its one-equality-filter rule is why every /students/me/* endpoint carries a
`sample_size` parameter - those endpoints are GROUP BY queries executed in
Python because the store cannot express them.

The application side of the migration is nothing: build_storage() picks its
backend from environment variables alone, and MongoStorage already exposes the
identical 31-method interface. This script exists only to move the rows.
=========================================================================
"""

from __future__ import annotations

import argparse
import sys

from app.core.config import get_settings

# The eight collections, and the field each one is keyed on.
#
# These are not guesses: each is the field MongoStorage.create_indexes() marks
# UNIQUE for that collection. Keying the copy on the same natural id means a
# re-run updates rather than duplicates - and getting one wrong is how you run a
# migration twice and find half of it doubled. conceptMastery is keyed on
# masteryId, not the conceptMasteryId the collection name suggests.
COLLECTIONS = {
    "users": "userId",
    "authSessions": "authSessionId",
    "learningSessions": "learningSessionId",
    "codeDiagnostics": "diagnosticRecordId",
    "learningEvents": "eventId",
    "collaborationSessions": "pairSessionId",
    "remediationTriggers": "triggerId",
    "conceptMastery": "masteryId",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write to MongoDB")
    args = parser.parse_args()

    settings = get_settings()

    if not settings.mongodb_uri:
        raise SystemExit("MONGODB_URI is not set - nothing to migrate into.")

    # Firestore is reached directly rather than through build_storage(), because
    # by the time anyone runs this the FIREBASE_* variables may already have been
    # unset - and then build_storage() would hand back the Mongo backend and this
    # would cheerfully copy Mongo onto itself.
    try:
        from google.cloud import firestore
    except ImportError:
        raise SystemExit(
            "google-cloud-firestore is not installed. It was removed from "
            "requirements-prod.txt as part of this migration; install it "
            "temporarily to run this script:  pip install google-cloud-firestore"
        )

    if settings.firebase_credentials_path:
        source = firestore.Client.from_service_account_json(settings.firebase_credentials_path)
    elif settings.firebase_project_id:
        source = firestore.Client(project=settings.firebase_project_id)
    else:
        raise SystemExit(
            "Neither FIREBASE_CREDENTIALS_PATH nor FIREBASE_PROJECT_ID is set, so "
            "there is no Firestore to read from. If you have already switched "
            "over, set one of them temporarily to run this."
        )

    from pymongo import MongoClient

    target = MongoClient(settings.mongodb_uri)[settings.mongodb_db_name]

    print("=" * 66)
    print("  APPLYING" if args.apply else "  DRY RUN - nothing will be written")
    print(f"  {source.project}  ->  {settings.mongodb_db_name}")
    print("=" * 66)

    grand_total = 0
    for name, key in COLLECTIONS.items():
        documents = [d.to_dict() for d in source.collection(name).stream()]
        existing = target[name].count_documents({}) if args.apply else target[name].count_documents({})

        missing_key = sum(1 for doc in documents if not doc.get(key))
        note = f"  ({missing_key} without {key}, will be inserted unkeyed)" if missing_key else ""
        print(f"  {name:24} {len(documents):5} in Firestore, {existing:5} already in Mongo{note}")

        if not args.apply or not documents:
            grand_total += len(documents)
            continue

        for doc in documents:
            identifier = doc.get(key)
            if identifier:
                target[name].update_one({key: identifier}, {"$set": doc}, upsert=True)
            else:
                target[name].insert_one(doc)

        grand_total += len(documents)

    if args.apply:
        # Recreate the indexes MongoStorage expects. Without them the platform
        # still works and then degrades quietly as the data grows, which is a
        # much harder problem to notice than a missing collection.
        from app.db.storage import MongoStorage

        MongoStorage(settings.mongodb_uri, settings.mongodb_db_name).create_indexes()
        print("\n  indexes created")

        print("\n  verification (Mongo counts after the copy):")
        for name in COLLECTIONS:
            print(f"    {name:24} {target[name].count_documents({}):5}")

    print("\n" + "=" * 66)
    print(f"  {grand_total} document(s) " + ("migrated" if args.apply else "would be migrated"))
    if not args.apply:
        print("  re-run with --apply to write")
    print("=" * 66)


if __name__ == "__main__":
    main()
