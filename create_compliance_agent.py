#!/usr/bin/env python3
"""
Create a Compliance QA agent for the Tasco demo app.
This creates a simple single-agent (no workers) for testing chat functionality.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from sdk import BlueprintClient, BlueprintConfig, AgentConfig

def create_compliance_qa_agent():
    """Create a Compliance QA agent blueprint."""

    # Initialize client
    client = BlueprintClient(
        agent_api_key=os.getenv("LYZR_API_KEY"),
        blueprint_bearer_token=os.getenv("BLUEPRINT_BEARER_TOKEN"),
        organization_id=os.getenv("LYZR_ORG_ID"),
    )

    # Define the Compliance QA agent (manager)
    manager = AgentConfig(
        name="Compliance QA Assistant",
        description="AI assistant for Tasco Group compliance and policy questions",
        role="Compliance and Governance Specialist",
        goal="Help employees find answers to compliance, policy, and governance questions with accurate citations",
        instructions="""You are the Compliance QA Assistant for Tasco Group, a diversified conglomerate with subsidiaries across automotive, insurance, water utilities, and holding companies.

Your role is to help employees understand company policies, compliance requirements, and governance procedures.

When answering questions:
1. Be specific and cite relevant policies or documents when possible
2. If you don't know something, say so clearly
3. For complex compliance matters, recommend consulting with the legal or compliance team
4. Keep answers clear and actionable

Key areas you can help with:
- Travel and expense policies
- Contract approval processes
- Capital expenditure authorities
- Compliance reporting requirements
- Data privacy and security policies
- Ethics and code of conduct
- Audit and governance procedures

Always maintain a professional, helpful tone and prioritize accuracy over speed.""",
        model="gpt-4o-mini",
        temperature=0.3,
        features=["memory"],  # Enable conversation memory
    )

    # Define a simple worker for document retrieval
    doc_worker = AgentConfig(
        name="Document Retriever",
        description="Retrieves relevant compliance documents and policies",
        role="Document Research Specialist",
        goal="Find and retrieve relevant policy documents and compliance information",
        instructions="""You help find relevant documents and policies from the Tasco Group knowledge base.

When asked to find information:
1. Search for relevant policy documents
2. Extract key sections that answer the question
3. Provide document names and page references when available
4. Summarize key points clearly

Focus on accuracy and always cite your sources.""",
        model="gpt-4o-mini",
        temperature=0.2,
        usage_description="Use for finding and retrieving relevant compliance documents and policies",
    )

    # Create blueprint config
    config = BlueprintConfig(
        name="Tasco Compliance QA",
        description="AI assistant for Tasco Group compliance, policy, and governance questions. Helps employees find answers with accurate citations.",
        manager=manager,
        workers=[doc_worker],
        category="legal",
        tags=["compliance", "policy", "governance", "qa", "tasco"],
        visibility="organization",
    )

    # Validate configuration
    print("Validating configuration...")
    report = client.doctor_config(config)
    if not report.valid:
        print(f"Validation errors: {report.errors}")
        for error in report.errors:
            print(f"  - {error}")
        return None
    print("Configuration valid!")

    # Create the blueprint
    print("\nCreating blueprint...")
    blueprint = client.create(config)

    print("\n" + "=" * 60)
    print("Blueprint created successfully!")
    print("=" * 60)
    print(f"\nBlueprint ID: {blueprint.id}")
    print(f"Manager Agent ID: {blueprint.manager_id}")
    print(f"\nStudio URL: {blueprint.studio_url}")
    print(f"Marketplace URL: {blueprint.marketplace_url}")

    print("\n" + "-" * 60)
    print("Use these values in your Tasco compliance-qa app:")
    print("-" * 60)
    print(f"LYZR_AGENT_ID={blueprint.manager_id}")
    print(f"LYZR_API_KEY={os.getenv('LYZR_API_KEY')}")

    return blueprint


if __name__ == "__main__":
    blueprint = create_compliance_qa_agent()
    if blueprint:
        print("\n\nDone! You can now use the agent in your chat application.")
