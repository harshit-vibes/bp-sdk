#!/usr/bin/env python3
"""
Diagnostic script to find blueprints with data issues that cause 500 errors.

Usage:
    # With environment variable
    MONGO_DB_URL='mongodb://...' python scripts/find_problematic_blueprints.py

    # Or edit the MONGO_URL below directly
"""

import os
from pymongo import MongoClient

# Production MongoDB URL (set via env or edit here)
MONGO_URL = os.environ.get("MONGO_DB_URL", "")
ORG_ID = "b385ab96-1dd1-489b-8f7e-f5d10f9edd7e"  # Your org
OWNER_ID = "mem_cmh4p1sx808p90rmxhrr63lqx"  # Your user ID


def find_problematic_blueprints():
    """Find blueprints with null/invalid fields that cause serialization errors."""

    if not MONGO_URL:
        print("ERROR: Set MONGO_DB_URL environment variable")
        print("Example: MONGO_DB_URL='mongodb://...' python scripts/find_problematic_blueprints.py")
        return

    client = MongoClient(MONGO_URL)

    # Find the correct database (production uses different DB name)
    db_names = client.list_database_names()
    print(f"Available databases: {db_names}")

    # Try common database names
    for db_name in ["agent_studio", "agent_studio_prod", "pagos", "pagos_prod"]:
        if db_name in db_names:
            db = client[db_name]
            if "blueprints" in db.list_collection_names():
                print(f"\nUsing database: {db_name}")
                break
    else:
        # Fall back to admin or first available
        db = client.get_default_database() or client["admin"]
        print(f"\nUsing database: {db.name}")

    blueprints = db.blueprints

    # Query 1: Find blueprints with null/missing required fields
    print("\n--- Blueprints with NULL/missing required fields ---")
    null_fields_query = {
        "organization_id": ORG_ID,
        "$or": [
            {"orchestration_type": None},
            {"orchestration_type": {"$exists": False}},
            {"orchestration_name": None},
            {"orchestration_name": {"$exists": False}},
            {"blueprint_data": None},
            {"shared_with_users": None},
            {"shared_with_organizations": None},
            {"owner_id": None},
            {"name": None},
        ]
    }

    for bp in blueprints.find(null_fields_query, {"_id": 1, "name": 1, "owner_id": 1}):
        print(f"  ID: {bp.get('_id')} | Name: {bp.get('name')} | Owner: {bp.get('owner_id')}")

    # Query 2: Find blueprints where arrays are not arrays
    print("\n--- Blueprints with wrong types for array fields ---")
    wrong_type_query = {
        "organization_id": ORG_ID,
        "$or": [
            {"shared_with_users": {"$not": {"$type": "array"}, "$ne": None}},
            {"shared_with_organizations": {"$not": {"$type": "array"}, "$ne": None}},
            {"tags": {"$not": {"$type": "array"}, "$ne": None}},
        ]
    }

    for bp in blueprints.find(wrong_type_query, {"_id": 1, "name": 1, "owner_id": 1}):
        print(f"  ID: {bp.get('_id')} | Name: {bp.get('name')} | Owner: {bp.get('owner_id')}")

    # Query 3: Find blueprints with non-object blueprint_data
    print("\n--- Blueprints with invalid blueprint_data ---")
    invalid_data_query = {
        "organization_id": ORG_ID,
        "blueprint_data": {"$not": {"$type": "object"}}
    }

    for bp in blueprints.find(invalid_data_query, {"_id": 1, "name": 1, "owner_id": 1}):
        print(f"  ID: {bp.get('_id')} | Name: {bp.get('name')} | Owner: {bp.get('owner_id')}")

    # Query 4: List all blueprints by owner to verify count
    print(f"\n--- All blueprints owned by {OWNER_ID} ---")
    all_mine = list(blueprints.find(
        {"organization_id": ORG_ID, "owner_id": OWNER_ID},
        {"_id": 1, "name": 1, "share_type": 1, "created_at": 1}
    ).sort("created_at", -1))

    print(f"Total: {len(all_mine)}")
    for i, bp in enumerate(all_mine[:10], 1):
        print(f"  {i}. {bp.get('_id')} | {bp.get('name')[:40] if bp.get('name') else 'NO NAME'} | {bp.get('share_type')}")

    if len(all_mine) > 10:
        print(f"  ... and {len(all_mine) - 10} more")

    client.close()


def try_serialize_all():
    """
    Alternative approach: Try to serialize each blueprint and catch errors.
    This mimics what pagos does and finds exactly which blueprints fail.
    """
    from pydantic import BaseModel, validator
    from typing import Optional, List, Dict, Any
    from enum import Enum
    from datetime import datetime

    class ShareType(str, Enum):
        PRIVATE = "private"
        PUBLIC = "public"
        ORGANIZATION = "organization"

    class OrchestrationType(str, Enum):
        SIMPLE = "simple"
        MULTI_AGENT = "multi_agent"

    class BlueprintResponse(BaseModel):
        """Minimal version of pagos BlueprintResponse"""
        blueprint_id: str
        name: str
        description: Optional[str] = None
        orchestration_type: OrchestrationType
        orchestration_name: str
        share_type: ShareType = ShareType.PRIVATE
        owner_id: str
        organization_id: str
        blueprint_data: Dict[str, Any] = {}
        tags: List[str] = []
        shared_with_users: List[str] = []
        shared_with_organizations: List[str] = []
        created_at: Optional[datetime] = None
        updated_at: Optional[datetime] = None

        class Config:
            extra = "allow"

        @validator('shared_with_users', 'shared_with_organizations', 'tags', pre=True)
        def ensure_list(cls, v):
            if v is None:
                return []
            return v

    if not MONGO_URL:
        print("ERROR: Set MONGO_DB_URL")
        return

    client = MongoClient(MONGO_URL)
    db = client.get_default_database() or client["admin"]

    # Try to find the blueprints collection
    if "blueprints" not in db.list_collection_names():
        for db_name in client.list_database_names():
            if "blueprints" in client[db_name].list_collection_names():
                db = client[db_name]
                break

    blueprints = db.blueprints

    print(f"\n--- Testing serialization for all blueprints in org {ORG_ID} ---")

    query = {"organization_id": ORG_ID}
    total = blueprints.count_documents(query)
    print(f"Found {total} blueprints to test")

    failed = []
    success = 0

    for bp in blueprints.find(query):
        try:
            # Mimic what pagos does
            response_data = {
                "blueprint_id": str(bp.get("_id")),
                "name": bp.get("name"),
                "description": bp.get("description"),
                "orchestration_type": bp.get("orchestration_type"),
                "orchestration_name": bp.get("orchestration_name"),
                "share_type": bp.get("share_type"),
                "owner_id": bp.get("owner_id"),
                "organization_id": bp.get("organization_id"),
                "blueprint_data": bp.get("blueprint_data", {}),
                "tags": bp.get("tags", []),
                "shared_with_users": bp.get("shared_with_users", []),
                "shared_with_organizations": bp.get("shared_with_organizations", []),
                "created_at": bp.get("created_at"),
                "updated_at": bp.get("updated_at"),
            }

            # Try to serialize
            BlueprintResponse(**response_data)
            success += 1

        except Exception as e:
            failed.append({
                "id": str(bp.get("_id")),
                "name": bp.get("name"),
                "error": str(e),
                "data": {
                    "orchestration_type": bp.get("orchestration_type"),
                    "orchestration_name": bp.get("orchestration_name"),
                    "share_type": bp.get("share_type"),
                    "blueprint_data_type": type(bp.get("blueprint_data")).__name__,
                }
            })

    print(f"\nResults: {success} success, {len(failed)} failed")

    if failed:
        print("\n--- FAILED BLUEPRINTS ---")
        for f in failed:
            print(f"\nID: {f['id']}")
            print(f"Name: {f['name']}")
            print(f"Error: {f['error']}")
            print(f"Data: {f['data']}")

    client.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--serialize":
        try_serialize_all()
    else:
        find_problematic_blueprints()
