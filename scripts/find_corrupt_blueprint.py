#!/usr/bin/env python3
"""
Find corrupt blueprints by testing each against Pydantic validation.

Usage:
    # Set production MongoDB URL first
    export MONGO_DB_URL="mongodb+srv://..."

    python scripts/find_corrupt_blueprint.py
"""

import os
import sys
from datetime import datetime

# Add the pagos app to path for models
PAGOS_PATH = "/Users/harshitchoudhary/Documents/Work/Lyzr/services/main/pagos"
sys.path.insert(0, PAGOS_PATH)

try:
    from pymongo import MongoClient
except ImportError:
    print("ERROR: pymongo not installed. Run: pip install pymongo")
    sys.exit(1)


def main():
    # Configuration
    mongo_url = os.getenv("MONGO_DB_URL")
    if not mongo_url:
        print("ERROR: Set MONGO_DB_URL environment variable")
        print("  export MONGO_DB_URL='mongodb+srv://...'")
        sys.exit(1)

    db_name = os.getenv("DBNAME", "agent_studio")
    owner_id = "mem_cmh4p1sx808p90rmxhrr63lqx"
    org_id = "b385ab96-1dd1-489b-8f7e-f5d10f9edd7e"

    print(f"Connecting to MongoDB...")
    print(f"Database: {db_name}")
    print(f"Owner ID: {owner_id}")
    print(f"Org ID: {org_id}")
    print()

    # Connect to MongoDB
    client = MongoClient(mongo_url)
    db = client[db_name]
    collection = db["blueprints"]

    # Query for user's blueprints
    query = {
        "$or": [
            {"owner_id": owner_id},
            {"organization_id": org_id}
        ]
    }

    blueprints = list(collection.find(query))
    print(f"Found {len(blueprints)} blueprints for this user/org")
    print()

    # Try to import and validate each against Pydantic model
    try:
        from app.blueprints.models import BlueprintResponse

        print("Testing each blueprint against Pydantic validation...")
        print("-" * 60)

        corrupt_blueprints = []

        for bp in blueprints:
            bp_id = bp.get("_id", "unknown")
            bp_name = bp.get("name", "unknown")

            try:
                # This is what the API does - try to create a response model
                BlueprintResponse(**bp)
                print(f"✓ {bp_id[:8]}... {bp_name[:40]}")
            except Exception as e:
                print(f"✗ {bp_id} - {bp_name}")
                print(f"  ERROR: {str(e)[:200]}")
                corrupt_blueprints.append({
                    "id": bp_id,
                    "name": bp_name,
                    "error": str(e),
                    "raw_data": bp
                })

        print("-" * 60)
        print()

        if corrupt_blueprints:
            print(f"FOUND {len(corrupt_blueprints)} CORRUPT BLUEPRINT(S):")
            print()
            for cb in corrupt_blueprints:
                print(f"  Blueprint ID: {cb['id']}")
                print(f"  Name: {cb['name']}")
                print(f"  Error: {cb['error'][:300]}")
                print()
                print("  To delete, run:")
                print(f"    bp delete {cb['id']}")
                print()
        else:
            print("No corrupt blueprints found via Pydantic validation.")
            print()
            print("The issue might be in the response serialization layer.")
            print("Listing all blueprint IDs for manual inspection:")
            print()
            for bp in blueprints:
                created = bp.get("created_at", "unknown")
                updated = bp.get("updated_at", "unknown")
                print(f"  {bp['_id']} | {bp.get('name', 'unnamed')[:30]} | updated: {updated}")

    except ImportError as e:
        print(f"Could not import Pydantic models: {e}")
        print()
        print("Listing all blueprint IDs instead:")
        print("-" * 60)
        for bp in blueprints:
            print(f"  ID: {bp['_id']}")
            print(f"  Name: {bp.get('name', 'unnamed')}")
            print(f"  Category: {bp.get('category', 'unknown')}")
            print(f"  Share Type: {bp.get('share_type', 'unknown')}")
            print(f"  Updated: {bp.get('updated_at', 'unknown')}")
            print()

    client.close()


if __name__ == "__main__":
    main()
