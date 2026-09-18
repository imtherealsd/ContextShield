"""Seeds ContextShield baseline security policies into the Moss Local Runtime index."""

import asyncio
import json
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from moss import DocumentInfo, MossClient
except ImportError:
    print("Error: 'moss' package is not installed. Run 'pip install moss' first.")
    sys.exit(1)


async def seed_policies(
    project_id: str,
    project_key: str,
    index_name: str,
    policies_path: Path
) -> None:
    """Seeds the 20 ContextShield policies into the specified Moss index."""
    if not policies_path.exists():
        raise FileNotFoundError(f"Policies dataset not found at {policies_path}")

    with open(policies_path, "r", encoding="utf-8") as f:
        policies_data = json.load(f)

    print(f"Loaded {len(policies_data)} policies from {policies_path}")

    # Build DocumentInfo objects without manual embeddings (Moss SDK requires Dict[str, str] for metadata)
    docs = [
        DocumentInfo(
            id=item["id"],
            text=item["text"],
            metadata={
                k: str(v).lower() if isinstance(v, bool) else str(v)
                for k, v in item.get("metadata", {}).items()
            }
        )
        for item in policies_data
    ]

    client = MossClient(project_id, project_key)

    print("Checking existing indexes in Moss...")
    existing_indexes = await client.list_indexes()
    existing_names = [idx.name for idx in existing_indexes]

    if index_name in existing_names:
        print(f"Index '{index_name}' exists. Adding/mutating {len(docs)} documents...")
        mutation_result = await client.add_docs(index_name, docs)
        print(f"Successfully updated index '{index_name}': {mutation_result}")
    else:
        print(f"Index '{index_name}' does not exist. Creating index with {len(docs)} documents...")
        create_result = await client.create_index(index_name, docs, wait=True)
        print(f"Successfully created index '{index_name}': {create_result}")


def main():
    project_id = os.getenv("MOSS_PROJECT_ID")
    project_key = os.getenv("MOSS_PROJECT_KEY")
    index_name = os.getenv("MOSS_INDEX_NAME", "contextshield-security")

    if not project_id or not project_key:
        print("Error: MOSS_PROJECT_ID and MOSS_PROJECT_KEY environment variables must be set.")
        print("Please configure them in your environment or in a .env file.")
        sys.exit(1)

    repo_root = Path(__file__).resolve().parent.parent
    policies_path = repo_root / "backend" / "app" / "data" / "security_policies.json"

    asyncio.run(seed_policies(project_id, project_key, index_name, policies_path))


if __name__ == "__main__":
    main()
