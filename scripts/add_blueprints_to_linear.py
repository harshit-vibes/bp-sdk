"""Add 30 new blueprint tasks to Linear backlog."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import httpx

load_dotenv(Path(__file__).parent.parent / ".env")

LINEAR_API_KEY = os.getenv('LINEAR_API_KEY')
TEAM_ID = os.getenv('LINEAR_TEAM_ID')
PROJECT_ID = '8b7c8685-baf9-496d-bff4-bcad19b4eecd'
BACKLOG_STATE = 'c63fce57-95ca-4cb4-8a25-891c927a92f1'

blueprints = [
    # SECURITY (5)
    ("BP-082", "Security Vulnerability Scanner", "security", "Scans code repositories for security vulnerabilities, generates remediation reports"),
    ("BP-083", "SOC Alert Triage Agent", "security", "Triages security alerts, prioritizes by severity, suggests response actions"),
    ("BP-084", "Phishing Email Detector", "security", "Analyzes emails for phishing indicators, explains red flags to users"),
    ("BP-085", "Access Control Auditor", "security", "Reviews user permissions across systems, identifies over-privileged accounts"),
    ("BP-086", "Security Incident Playbook", "security", "Guides security teams through incident response with step-by-step actions"),

    # PRODUCT (4)
    ("BP-087", "Product Requirements Document Writer", "product", "Transforms user research into structured PRDs with acceptance criteria"),
    ("BP-088", "Feature Prioritization Assistant", "product", "Applies RICE/ICE/MoSCoW frameworks to prioritize product backlog"),
    ("BP-089", "User Feedback Synthesizer", "product", "Aggregates and synthesizes user feedback into actionable insights"),
    ("BP-090", "Competitive Intelligence Analyst", "product", "Monitors competitors, generates comparison matrices and battlecards"),

    # DATA (4)
    ("BP-091", "Natural Language to SQL", "data", "Converts business questions into SQL queries with explanations"),
    ("BP-092", "Data Quality Auditor", "data", "Validates datasets for completeness, accuracy, and consistency"),
    ("BP-093", "Dashboard Insight Generator", "data", "Analyzes dashboard data, generates executive summaries and insights"),
    ("BP-094", "A/B Test Results Analyzer", "data", "Analyzes experiment results, calculates significance, recommends actions"),

    # PEOPLE (3)
    ("BP-095", "Interview Question Generator", "people", "Creates role-specific behavioral and technical interview questions"),
    ("BP-096", "Performance Review Assistant", "people", "Helps managers write balanced, constructive performance reviews"),
    ("BP-097", "Learning Path Recommender", "people", "Recommends personalized training and development paths"),

    # SALES (3)
    ("BP-098", "Deal Risk Analyzer", "sales", "Identifies at-risk deals, suggests recovery strategies"),
    ("BP-099", "Competitive Battlecard Generator", "sales", "Creates sales battlecards with competitor weaknesses and responses"),
    ("BP-100", "Quote Configuration Assistant", "sales", "Guides reps through complex quote configuration with guardrails"),

    # MARKETING (3)
    ("BP-101", "SEO Content Optimizer", "marketing", "Analyzes and optimizes content for search engine rankings"),
    ("BP-102", "Influencer Research Agent", "marketing", "Identifies relevant influencers, analyzes engagement metrics"),
    ("BP-103", "Landing Page Copy Generator", "marketing", "Writes conversion-focused landing page copy with A/B variants"),

    # CUSTOMER (2)
    ("BP-104", "Customer Health Scorer", "customer", "Calculates customer health scores, predicts churn risk"),
    ("BP-105", "Onboarding Journey Builder", "customer", "Creates personalized customer onboarding checklists and milestones"),

    # FINANCE (2)
    ("BP-106", "Expense Report Processor", "finance", "Categorizes expenses, checks policy compliance, flags anomalies"),
    ("BP-107", "Invoice Data Extractor", "finance", "Extracts structured data from invoices, validates against POs"),

    # LEGAL (1)
    ("BP-108", "Privacy Policy Analyzer", "legal", "Analyzes privacy policies, identifies compliance gaps with GDPR/CCPA"),

    # TECH (1)
    ("BP-109", "API Documentation Generator", "tech", "Generates OpenAPI specs and developer documentation from code"),

    # FEATURED (2)
    ("BP-110", "Claude Artifacts Multi-Output", "featured", "Generates multiple artifact types (code, docs, diagrams) in parallel"),
    ("BP-111", "Chain of Verification (CoVe)", "featured", "Verifies LLM outputs through systematic fact-checking pipeline"),
]


def main():
    print(f"Creating {len(blueprints)} issues in BP Library backlog...")
    print()

    success = 0
    for bp_id, name, category, description in blueprints:
        title = f"[{bp_id}] {name}"

        mutation = '''
        mutation {
          issueCreate(input: {
            teamId: "%s",
            projectId: "%s",
            stateId: "%s",
            title: "%s",
            description: "%s\\n\\n**Category:** %s"
          }) {
            success
            issue { identifier title }
          }
        }
        ''' % (TEAM_ID, PROJECT_ID, BACKLOG_STATE, title, description, category)

        resp = httpx.post(
            'https://api.linear.app/graphql',
            headers={'Authorization': LINEAR_API_KEY, 'Content-Type': 'application/json'},
            json={'query': mutation}
        )

        result = resp.json()
        if result.get('data', {}).get('issueCreate', {}).get('success'):
            issue = result['data']['issueCreate']['issue']
            print(f"  ✓ {issue['identifier']}: {name} [{category}]")
            success += 1
        else:
            print(f"  ✗ Failed: {name}")
            print(f"    Error: {result}")

    print(f"\nDone! {success}/{len(blueprints)} created in Backlog")


if __name__ == "__main__":
    main()
