#!/usr/bin/env python3
"""Find corrupt blueprints causing 500 errors.

This script identifies blueprints with invalid data that cause Pydantic
validation failures in the list_blueprints endpoint.

Approaches:
1. Binary search through pages to find failing page
2. Then linear search within that page to find specific blueprint
3. Report blueprint IDs for deletion/fixing

Usage:
    python scripts/find_corrupt_blueprints.py

Environment variables:
    BLUEPRINT_BEARER_TOKEN - Pagos API bearer token
    LYZR_ORG_ID - Organization ID
"""

import os
import sys
from pathlib import Path
from typing import Any

# Load .env file
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

import httpx

# Configuration
PAGOS_URL = os.getenv("PAGOS_URL", "https://pagos-prod.studio.lyzr.ai")
BEARER_TOKEN = os.getenv("BLUEPRINT_BEARER_TOKEN", "")
ORG_ID = os.getenv("LYZR_ORG_ID", "")


def get_headers() -> dict:
    return {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json",
    }


def list_blueprints_raw(page: int = 1, page_size: int = 50) -> tuple[int, Any]:
    """Fetch blueprints without Pydantic validation.

    Returns:
        Tuple of (status_code, response_data_or_error)
    """
    url = f"{PAGOS_URL}/api/v1/blueprints/blueprints"
    params = {
        "user_organization_id": ORG_ID,
        "page": page,
        "page_size": page_size,
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=get_headers(), params=params)
            if response.status_code == 200:
                return 200, response.json()
            else:
                return response.status_code, response.text
    except Exception as e:
        return 0, str(e)


def get_blueprint_by_id(blueprint_id: str) -> tuple[int, Any]:
    """Fetch a single blueprint by ID."""
    url = f"{PAGOS_URL}/api/v1/blueprints/blueprints/{blueprint_id}"
    params = {"organization_id": ORG_ID}

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=get_headers(), params=params)
            if response.status_code == 200:
                return 200, response.json()
            else:
                return response.status_code, response.text
    except Exception as e:
        return 0, str(e)


def validate_blueprint_structure(bp: dict) -> list[str]:
    """Check blueprint for common corruption issues.

    Returns list of issues found.
    """
    issues = []
    bp_id = bp.get("_id", "unknown")

    # Check required fields
    if not bp.get("name"):
        issues.append(f"{bp_id}: Missing name")

    if not bp.get("blueprint_data"):
        issues.append(f"{bp_id}: Missing blueprint_data")
        return issues  # Can't check further

    bd = bp["blueprint_data"]

    # Check for None values that should be arrays
    array_fields = [
        "agents", "nodes", "edges",
    ]
    for field in array_fields:
        if field in bd and bd[field] is None:
            issues.append(f"{bp_id}: blueprint_data.{field} is None (should be [] or {{}})")

    # Check agents structure
    agents = bd.get("agents", {})
    if isinstance(agents, dict):
        for agent_id, agent_data in agents.items():
            if agent_data is None:
                issues.append(f"{bp_id}: agents[{agent_id}] is None")
                continue

            # Check agent array fields
            agent_array_fields = [
                "managed_agents", "tool_configs", "features", "tools",
                "files", "artifacts", "personas", "messages", "a2a_tools"
            ]
            for field in agent_array_fields:
                if field in agent_data and agent_data[field] is None:
                    issues.append(f"{bp_id}: agents[{agent_id}].{field} is None")

    # Check root-level array fields
    root_array_fields = [
        "tags", "shared_with_users", "shared_with_organizations",
        "user_ids", "organization_ids", "permissions"
    ]
    for field in root_array_fields:
        if field in bp and bp[field] is None:
            issues.append(f"{bp_id}: {field} is None (should be [])")

    # Check for missing manager_agent_id
    if not bd.get("manager_agent_id"):
        issues.append(f"{bp_id}: Missing manager_agent_id")

    return issues


def find_corrupt_blueprints():
    """Main function to find corrupt blueprints."""

    if not BEARER_TOKEN:
        print("ERROR: BLUEPRINT_BEARER_TOKEN not set")
        sys.exit(1)
    if not ORG_ID:
        print("ERROR: LYZR_ORG_ID not set")
        sys.exit(1)

    print(f"Searching for corrupt blueprints...")
    print(f"Pagos URL: {PAGOS_URL}")
    print(f"Org ID: {ORG_ID[:8]}...")
    print()

    # Step 1: Try fetching with small page size to test connectivity
    print("Step 1: Testing API connectivity...")
    status, data = list_blueprints_raw(page=1, page_size=1)
    if status != 200:
        print(f"ERROR: API returned {status}: {data}")
        sys.exit(1)

    total = data.get("total", 0)
    print(f"Total blueprints: {total}")
    print()

    if total == 0:
        print("No blueprints found.")
        return

    # Step 2: Find pages that fail with larger page sizes
    print("Step 2: Testing different page sizes...")

    for page_size in [10, 25, 50]:
        status, data = list_blueprints_raw(page=1, page_size=page_size)
        if status == 200:
            print(f"  page_size={page_size}: OK ({len(data.get('blueprints', []))} returned)")
        else:
            print(f"  page_size={page_size}: FAILED ({status})")
    print()

    # Step 3: Scan all blueprints one by one for structural issues
    print("Step 3: Scanning all blueprints for structural issues...")

    all_issues = []
    corrupt_ids = set()
    page = 1
    page_size = 10  # Use small page size to avoid 500 errors

    while True:
        status, data = list_blueprints_raw(page=page, page_size=page_size)

        if status != 200:
            print(f"  Page {page} failed with status {status}")
            # Try fetching one by one
            print(f"  Trying to fetch page {page} items individually...")

            # Calculate offset
            start_idx = (page - 1) * page_size

            # We can't get individual items from a failed page without IDs
            # Mark this page as problematic
            print(f"  WARNING: Could not fetch page {page}. Corrupt blueprint likely in range {start_idx}-{start_idx + page_size}")
            break

        blueprints = data.get("blueprints", [])
        if not blueprints:
            break

        for bp in blueprints:
            issues = validate_blueprint_structure(bp)
            if issues:
                bp_id = bp.get("_id", "unknown")
                corrupt_ids.add(bp_id)
                all_issues.extend(issues)
                print(f"  Found issues in blueprint: {bp_id}")
                for issue in issues:
                    print(f"    - {issue}")

        print(f"  Page {page}: Scanned {len(blueprints)} blueprints")

        if not data.get("has_more", False) and len(blueprints) < page_size:
            break

        page += 1

    print()

    # Step 4: Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    if corrupt_ids:
        print(f"\nFound {len(corrupt_ids)} blueprints with issues:")
        for bp_id in sorted(corrupt_ids):
            print(f"  - {bp_id}")

        print(f"\nTotal issues found: {len(all_issues)}")

        print("\n\nTo delete these blueprints, run:")
        for bp_id in sorted(corrupt_ids):
            print(f"  bp delete {bp_id}")
    else:
        print("\nNo structural issues found in scanned blueprints.")
        print("The 500 error may be caused by:")
        print("  1. Pydantic validation on optional fields")
        print("  2. Date parsing errors")
        print("  3. Enum validation failures")
        print("\nTry checking Pagos logs for the exact validation error.")


def scan_with_binary_search():
    """Use binary search to find the problematic page faster."""

    print("Using binary search to find failing page...")

    # First, find total count
    status, data = list_blueprints_raw(page=1, page_size=1)
    if status != 200:
        print(f"Cannot fetch even page_size=1: {status}")
        return

    total = data.get("total", 0)
    page_size = 50
    total_pages = (total + page_size - 1) // page_size

    print(f"Total: {total} blueprints, {total_pages} pages (page_size={page_size})")

    # Binary search for first failing page
    left, right = 1, total_pages
    first_failing_page = None

    while left <= right:
        mid = (left + right) // 2
        status, _ = list_blueprints_raw(page=mid, page_size=page_size)

        if status != 200:
            first_failing_page = mid
            right = mid - 1
            print(f"  Page {mid}: FAILED")
        else:
            left = mid + 1
            print(f"  Page {mid}: OK")

    if first_failing_page:
        print(f"\nFirst failing page: {first_failing_page}")
        print(f"Blueprints in range: {(first_failing_page-1)*page_size + 1} - {first_failing_page*page_size}")

        # Now scan that page with page_size=1
        print(f"\nScanning page {first_failing_page} one blueprint at a time...")

        start = (first_failing_page - 1) * page_size + 1
        for i in range(page_size):
            # We need to use skip/offset to get specific blueprints
            # Unfortunately the API uses page-based pagination, not offset
            # So we'll use page_size=1 and iterate
            status, data = list_blueprints_raw(page=start + i, page_size=1)
            if status != 200:
                print(f"  Blueprint at position {start + i}: FAILED")
            else:
                blueprints = data.get("blueprints", [])
                if blueprints:
                    bp_id = blueprints[0].get("_id", "unknown")
                    print(f"  Position {start + i}: {bp_id} - OK")
    else:
        print("\nNo failing pages found with page_size=50")


def try_public_endpoint():
    """Try fetching public blueprints which might not be affected."""
    print("Trying public browse endpoint...")

    url = f"{PAGOS_URL}/api/v1/blueprints/blueprints/public/browse"
    params = {"page": 1, "page_size": 10}

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, params=params)
            print(f"  Public browse: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Found {len(data.get('blueprints', []))} public blueprints")
    except Exception as e:
        print(f"  Error: {e}")


def try_direct_id_fetch():
    """Try fetching blueprints by direct ID if we have any."""
    print("\nTrying to get blueprint IDs from different sources...")

    # Try the bp list command output or stored IDs
    # For now, let's try the shared-with-me endpoint
    url = f"{PAGOS_URL}/api/v1/blueprints/blueprints/shared/with-me"
    params = {"organization_id": ORG_ID}

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=get_headers(), params=params)
            print(f"  Shared with me: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                blueprints = data if isinstance(data, list) else data.get('blueprints', [])
                print(f"  Found {len(blueprints)} shared blueprints")
                for bp in blueprints[:5]:
                    print(f"    - {bp.get('_id')}: {bp.get('name')}")
    except Exception as e:
        print(f"  Error: {e}")


def fetch_all_ids_via_projection():
    """Try to get just IDs using MongoDB projection (if API supports it)."""
    print("\nTrying to fetch blueprint IDs only...")

    # Try with minimal fields parameter if supported
    url = f"{PAGOS_URL}/api/v1/blueprints/blueprints"
    params = {
        "user_organization_id": ORG_ID,
        "page": 1,
        "page_size": 100,
    }

    # Some APIs support fields parameter for projection
    for fields_param in ["fields", "select", "projection"]:
        test_params = {**params, fields_param: "_id,name"}
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, headers=get_headers(), params=test_params)
                if response.status_code == 200:
                    print(f"  {fields_param} parameter works!")
                    data = response.json()
                    blueprints = data.get('blueprints', [])
                    print(f"  Found {len(blueprints)} blueprints")
                    return
        except:
            pass

    print("  No projection parameter supported")


def test_individual_visibilities():
    """Test different share_type filters to isolate the problem."""
    print("\nTesting different visibility filters...")

    url = f"{PAGOS_URL}/api/v1/blueprints/blueprints"

    for share_type in ["private", "public", "organization"]:
        params = {
            "user_organization_id": ORG_ID,
            "page": 1,
            "page_size": 10,
            "share_type": share_type,
        }
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, headers=get_headers(), params=params)
                if response.status_code == 200:
                    data = response.json()
                    count = len(data.get('blueprints', []))
                    total = data.get('total', 0)
                    print(f"  {share_type}: OK ({count} returned, {total} total)")
                else:
                    print(f"  {share_type}: FAILED ({response.status_code})")
        except Exception as e:
            print(f"  {share_type}: ERROR ({e})")


def scan_private_blueprints_one_by_one():
    """Scan private blueprints using page_size=1 to find the corrupt one."""
    print("\n" + "=" * 60)
    print("SCANNING PRIVATE BLUEPRINTS (page_size=1)")
    print("=" * 60)

    url = f"{PAGOS_URL}/api/v1/blueprints/blueprints"

    # First, check if page_size=1 works at all
    print("\nStep 1: Testing page_size=1 for private blueprints...")

    good_ids = []
    bad_positions = []
    position = 1
    consecutive_failures = 0
    max_consecutive_failures = 3

    while consecutive_failures < max_consecutive_failures:
        params = {
            "user_organization_id": ORG_ID,
            "page": position,
            "page_size": 1,
            "share_type": "private",
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, headers=get_headers(), params=params)

                if response.status_code == 200:
                    data = response.json()
                    blueprints = data.get('blueprints', [])

                    if not blueprints:
                        print(f"\n  Position {position}: No more blueprints")
                        break

                    bp = blueprints[0]
                    bp_id = bp.get('_id', 'unknown')
                    bp_name = bp.get('name', 'unnamed')[:30]
                    good_ids.append(bp_id)
                    consecutive_failures = 0

                    if position % 5 == 0 or position <= 3:
                        print(f"  Position {position}: OK - {bp_id[:20]}... ({bp_name})")

                else:
                    bad_positions.append(position)
                    consecutive_failures += 1
                    print(f"  Position {position}: FAILED ({response.status_code})")

                    # Try to get error details
                    try:
                        error_text = response.text[:200]
                        print(f"    Error: {error_text}")
                    except:
                        pass

        except Exception as e:
            bad_positions.append(position)
            consecutive_failures += 1
            print(f"  Position {position}: ERROR ({e})")

        position += 1

        # Safety limit
        if position > 100:
            print("\n  Reached safety limit of 100 positions")
            break

    print(f"\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Good blueprints found: {len(good_ids)}")
    print(f"Failed positions: {bad_positions}")

    if good_ids:
        print(f"\nBlueprint IDs that loaded successfully:")
        for bp_id in good_ids:
            print(f"  - {bp_id}")

    return good_ids, bad_positions


def fetch_blueprint_ids_via_alternative():
    """Try alternative methods to get blueprint IDs."""
    print("\n" + "=" * 60)
    print("ALTERNATIVE METHODS TO GET BLUEPRINT IDs")
    print("=" * 60)

    all_ids = set()

    # Method 1: Get from public blueprints
    print("\n1. Fetching from public blueprints...")
    url = f"{PAGOS_URL}/api/v1/blueprints/blueprints"
    params = {
        "user_organization_id": ORG_ID,
        "page": 1,
        "page_size": 100,
        "share_type": "public",
    }
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=get_headers(), params=params)
            if response.status_code == 200:
                data = response.json()
                for bp in data.get('blueprints', []):
                    all_ids.add(bp.get('_id'))
                print(f"   Got {len(data.get('blueprints', []))} public blueprint IDs")
    except Exception as e:
        print(f"   Failed: {e}")

    # Method 2: Get from organization blueprints
    print("\n2. Fetching from organization blueprints...")
    params["share_type"] = "organization"
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=get_headers(), params=params)
            if response.status_code == 200:
                data = response.json()
                for bp in data.get('blueprints', []):
                    all_ids.add(bp.get('_id'))
                print(f"   Got {len(data.get('blueprints', []))} organization blueprint IDs")
    except Exception as e:
        print(f"   Failed: {e}")

    # Method 3: Get from shared-with-me
    print("\n3. Fetching from shared-with-me endpoint...")
    url = f"{PAGOS_URL}/api/v1/blueprints/blueprints/shared/with-me"
    params = {"organization_id": ORG_ID}
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=get_headers(), params=params)
            if response.status_code == 200:
                data = response.json()
                blueprints = data if isinstance(data, list) else data.get('blueprints', [])
                for bp in blueprints:
                    all_ids.add(bp.get('_id'))
                print(f"   Got {len(blueprints)} shared blueprint IDs")
    except Exception as e:
        print(f"   Failed: {e}")

    print(f"\nTotal unique IDs collected: {len(all_ids)}")
    return all_ids


def test_individual_blueprint_by_id(blueprint_ids: set):
    """Test fetching individual blueprints by ID to find corrupt ones."""
    print("\n" + "=" * 60)
    print("TESTING INDIVIDUAL BLUEPRINTS BY ID")
    print("=" * 60)

    corrupt_ids = []
    ok_ids = []

    for i, bp_id in enumerate(blueprint_ids):
        if not bp_id:
            continue

        url = f"{PAGOS_URL}/api/v1/blueprints/blueprints/{bp_id}"
        params = {"organization_id": ORG_ID}

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, headers=get_headers(), params=params)

                if response.status_code == 200:
                    data = response.json()
                    # Try to validate the structure
                    issues = validate_blueprint_structure(data)
                    if issues:
                        corrupt_ids.append(bp_id)
                        print(f"  {bp_id[:20]}...: ISSUES FOUND")
                        for issue in issues:
                            print(f"    - {issue}")
                    else:
                        ok_ids.append(bp_id)
                        if (i + 1) % 10 == 0:
                            print(f"  Checked {i + 1}/{len(blueprint_ids)} blueprints...")
                else:
                    corrupt_ids.append(bp_id)
                    print(f"  {bp_id[:20]}...: FAILED ({response.status_code})")

        except Exception as e:
            corrupt_ids.append(bp_id)
            print(f"  {bp_id[:20]}...: ERROR ({e})")

    print(f"\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"OK blueprints: {len(ok_ids)}")
    print(f"Corrupt blueprints: {len(corrupt_ids)}")

    if corrupt_ids:
        print(f"\nCorrupt blueprint IDs:")
        for bp_id in corrupt_ids:
            print(f"  - {bp_id}")
            print(f"    Delete with: bp delete {bp_id}")

    return corrupt_ids


def diagnose_comprehensive():
    """Run comprehensive diagnosis."""
    if not BEARER_TOKEN:
        print("ERROR: BLUEPRINT_BEARER_TOKEN not set")
        sys.exit(1)
    if not ORG_ID:
        print("ERROR: LYZR_ORG_ID not set")
        sys.exit(1)

    print(f"Comprehensive Blueprint Diagnosis")
    print(f"=" * 60)
    print(f"Pagos URL: {PAGOS_URL}")
    print(f"Org ID: {ORG_ID[:8]}...")
    print()

    # Test 1: Public endpoint (no auth issues)
    try_public_endpoint()

    # Test 2: Different visibility filters
    test_individual_visibilities()

    # Test 3: Shared blueprints
    try_direct_id_fetch()

    # Test 4: Try projection
    fetch_all_ids_via_projection()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Find corrupt blueprints")
    parser.add_argument("--binary-search", action="store_true",
                       help="Use binary search to find failing page")
    parser.add_argument("--diagnose", action="store_true",
                       help="Run comprehensive diagnosis")
    parser.add_argument("--scan-private", action="store_true",
                       help="Scan private blueprints one by one (page_size=1)")
    parser.add_argument("--scan-all-ids", action="store_true",
                       help="Collect IDs from working endpoints and test each")
    args = parser.parse_args()

    if not BEARER_TOKEN:
        print("ERROR: BLUEPRINT_BEARER_TOKEN not set")
        sys.exit(1)
    if not ORG_ID:
        print("ERROR: LYZR_ORG_ID not set")
        sys.exit(1)

    print(f"Pagos URL: {PAGOS_URL}")
    print(f"Org ID: {ORG_ID[:8]}...")
    print()

    if args.binary_search:
        scan_with_binary_search()
    elif args.diagnose:
        diagnose_comprehensive()
    elif args.scan_private:
        scan_private_blueprints_one_by_one()
    elif args.scan_all_ids:
        ids = fetch_blueprint_ids_via_alternative()
        if ids:
            test_individual_blueprint_by_id(ids)
    else:
        find_corrupt_blueprints()
