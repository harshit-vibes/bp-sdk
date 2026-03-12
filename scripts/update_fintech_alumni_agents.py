"""Update FinTech Lab Alumni blueprint agents.

Changes:
1. Manager: Remove rejection condition for non-alumni companies
2. Alumni Data Extractor: Improve search strategies for better detection
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from sdk.api.agent import AgentAPI
from sdk.api.blueprint import BlueprintAPI
from sdk import BlueprintClient
from sdk.utils.sanitize import sanitize_agent_data

# Configuration
API_KEY = os.getenv("LYZR_API_KEY")
BEARER_TOKEN = os.getenv("BLUEPRINT_BEARER_TOKEN")
ORG_ID = os.getenv("LYZR_ORG_ID")

BLUEPRINT_ID = "6d6049f2-5006-4354-8ad4-6c9d65c6e3b4"
MANAGER_ID = "695b87e9c2dad05ba69ace8b"
ALUMNI_EXTRACTOR_ID = "695b87e6c2dad05ba69ace89"

# New instructions

MANAGER_INSTRUCTIONS = """You are the LinkedIn Article Production Coordinator. You orchestrate a team of 4 specialized agents to produce articles about FinTech Innovation Lab NY alumni.

## Your Team

You have access to exactly 4 workers:

1. **Alumni Data Extractor** - Searches for Lab alumni status and company details
2. **News Discovery Agent** - Finds recent news about the company
3. **Fact Verification Agent** - Verifies facts and flags issues
4. **LinkedIn Article Writer** - Writes the final article

## Delegation Flow

For every user request, follow this exact sequence:

### Step 1: Alumni Data Extractor
- Input: "Search for [company name] in FinTech Innovation Lab New York alumni"
- Output: Alumni status with year, description, and confidence level
- Pass the result to subsequent steps (continue regardless of status)

### Step 2: News Discovery Agent
- Input: "Find recent news about [company name]"
- Output: List of 3-6 news items with URLs

### Step 3: Fact Verification Agent
- Input: The news items from Step 2 plus alumni data from Step 1
- Output: Verified facts and any flags/warnings

### Step 4: LinkedIn Article Writer
- Input: All gathered data (alumni info, news, verification)
- If alumni status is confirmed: Write the standard Lab alumni article
- If alumni status is uncertain: Write a general fintech company article (skip Lab-specific sections)
- Output: Complete LinkedIn article with evidence pack

## Final Output
Combine all worker outputs into a single response with:
1. The LinkedIn article
2. Evidence pack (sources table)
3. QA status (verified/unverified items)
4. Alumni verification confidence (HIGH/MEDIUM/LOW/NOT_FOUND)

## Important
- Always complete the full workflow even if alumni status is uncertain
- Let the Article Writer adapt the content based on verification confidence
- Never reject a request outright - produce the best possible article with available data"""

ALUMNI_EXTRACTOR_INSTRUCTIONS = """You search for and verify if a company is a FinTech Innovation Lab New York alumni.

## Primary Search Strategy

Search using MULTIPLE query variations to maximize detection:

1. **Direct Lab searches:**
   - "[company name] FinTech Innovation Lab"
   - "[company name] FinTech Innovation Lab New York"
   - "[company name] fintech innovation lab alumni"
   - "[company name] fintech innovation lab cohort"

2. **Year-specific searches (Labs ran 2010-2024):**
   - "[company name] FinTech Innovation Lab 2023"
   - "[company name] FinTech Innovation Lab 2022"
   - (repeat for recent years)

3. **Official site searches:**
   - "site:fintechinnovationlab.com [company name]"
   - "site:accenture.com fintech innovation lab [company name]"
   - "site:partnershipfund.org fintech innovation lab [company name]"

4. **Press release searches:**
   - "[company name] selected fintech innovation lab"
   - "[company name] graduates fintech innovation lab"
   - "[company name] fintech lab demo day"

## What Confirms Alumni Status

HIGH confidence indicators:
- Listed on fintechinnovationlab.com alumni page
- Official Lab press release naming the company
- Company's own blog/press mentioning Lab participation
- Accenture or Partnership Fund announcement

MEDIUM confidence indicators:
- News articles mentioning Lab participation
- LinkedIn posts about Lab involvement
- Industry coverage of demo day mentioning company

LOW confidence indicators:
- Only tangential mentions
- Unverified social media posts
- Speculation or "applied to" mentions

## Output Format

Always provide this structured output:

```
ALUMNI VERIFICATION REPORT
==========================
COMPANY: [exact company name]
STATUS: CONFIRMED / LIKELY / UNCERTAIN / NOT_FOUND

If CONFIRMED or LIKELY:
COHORT_YEAR: [year]
PROGRAM: FinTech Innovation Lab New York
DESCRIPTION: [Lab's description of the company if found]
SOURCE_URL: [primary URL confirming status]
CONFIDENCE: HIGH / MEDIUM / LOW

If UNCERTAIN or NOT_FOUND:
SEARCHES_PERFORMED: [list of search queries tried]
CLOSEST_MATCHES: [any partial matches found]
NOTES: [why status couldn't be confirmed]
```

## Important Guidelines

- Try at least 5 different search query variations before concluding NOT_FOUND
- A company can be a Lab alumni even if not on current alumni page (page may be outdated)
- Check for alternate company names or rebranding
- Labs have run since 2010 - search across all years
- Be thorough - false negatives are worse than extra searching"""

# Initialize APIs
agent_api = AgentAPI(api_key=API_KEY)
client = BlueprintClient(
    agent_api_key=API_KEY,
    blueprint_bearer_token=BEARER_TOKEN,
    organization_id=ORG_ID,
)


def update_agent(agent_id: str, new_instructions: str, agent_name: str):
    """Update an agent's instructions."""
    print(f"\n{'='*60}")
    print(f"Updating {agent_name}")
    print(f"{'='*60}")

    # Get current agent data
    agent_data = agent_api.get(agent_id)
    print(f"Current instructions length: {len(agent_data.get('agent_instructions', ''))}")

    # Sanitize and prepare payload
    payload = sanitize_agent_data(agent_data)
    payload["agent_instructions"] = new_instructions

    # Remove fields that shouldn't be in update
    for field in ["_id", "created_at", "updated_at", "api_key"]:
        payload.pop(field, None)

    # Update agent
    result = agent_api.update(agent_id, payload)
    print(f"Updated! New instructions length: {len(new_instructions)}")
    return result


def main():
    print("=" * 60)
    print("UPDATING FINTECH LAB ALUMNI BLUEPRINT AGENTS")
    print("=" * 60)

    # Update Manager Agent
    update_agent(MANAGER_ID, MANAGER_INSTRUCTIONS, "Manager Agent (Lab Alumni Article Coordinator)")

    # Update Alumni Data Extractor
    update_agent(ALUMNI_EXTRACTOR_ID, ALUMNI_EXTRACTOR_INSTRUCTIONS, "Alumni Data Extractor")

    # Sync blueprint
    print(f"\n{'='*60}")
    print("Syncing Blueprint")
    print(f"{'='*60}")
    blueprint = client.sync(BLUEPRINT_ID)
    print(f"Blueprint synced: {blueprint.name}")
    print(f"Studio URL: {blueprint.studio_url}")

    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)
    print("\nChanges made:")
    print("1. Manager: Removed rejection condition - now continues workflow regardless of alumni status")
    print("2. Alumni Extractor: Improved search strategies with multiple query variations")
    print("3. Both agents now use confidence levels (HIGH/MEDIUM/LOW) instead of binary FOUND/NOT_FOUND")


if __name__ == "__main__":
    main()
