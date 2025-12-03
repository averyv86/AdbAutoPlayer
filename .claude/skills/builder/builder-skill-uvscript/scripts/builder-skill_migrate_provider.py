#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "click>=8.0.0",
# ]
# ///
"""
BaaS Migration Helper Tool

Generate migration scripts and checklists for moving between BaaS providers.
Analyzes schema differences, API changes, and data migration needs.

Usage:
    uv run migration_helper.py --from firebase --to supabase --components auth db storage
    uv run migration_helper.py --from auth0 --to clerk --components auth --json
"""

import json
import sys
from pathlib import Path
from typing import Any

import click


class BaaSMigrationHelper:
    """BaaS provider migration analysis and planning engine."""

    PROVIDERS = {
        "auth0": {"type": "auth", "api_type": "rest", "schema": "proprietary"},
        "clerk": {"type": "auth", "api_type": "rest", "schema": "proprietary"},
        "firebase_auth": {"type": "auth", "api_type": "firebase_sdk", "schema": "firebase"},
        "supabase": {"type": "database", "api_type": "rest+postgres", "schema": "postgres"},
        "neon": {"type": "database", "api_type": "postgres", "schema": "postgres"},
        "convex": {"type": "database", "api_type": "convex_sdk", "schema": "convex"},
        "firestore": {"type": "database", "api_type": "firebase_sdk", "schema": "firestore"},
        "vercel": {"type": "deployment", "api_type": "vercel_cli", "schema": "none"},
        "railway": {"type": "deployment", "api_type": "railway_cli", "schema": "none"},
    }

    MIGRATION_COMPLEXITY = {
        # Auth migrations
        ("auth0", "clerk"): {"complexity": "medium", "time": "4-6 hours", "data_migration": True},
        ("auth0", "firebase_auth"): {"complexity": "high", "time": "8-12 hours", "data_migration": True},
        ("clerk", "auth0"): {"complexity": "medium", "time": "6-8 hours", "data_migration": True},
        ("clerk", "firebase_auth"): {"complexity": "medium", "time": "4-6 hours", "data_migration": True},
        ("firebase_auth", "auth0"): {"complexity": "high", "time": "8-10 hours", "data_migration": True},
        ("firebase_auth", "clerk"): {"complexity": "medium", "time": "4-6 hours", "data_migration": True},
        # Database migrations
        ("firestore", "supabase"): {"complexity": "high", "time": "12-16 hours", "data_migration": True},
        ("firestore", "neon"): {"complexity": "high", "time": "10-14 hours", "data_migration": True},
        ("supabase", "neon"): {"complexity": "low", "time": "2-4 hours", "data_migration": True},
        ("neon", "supabase"): {"complexity": "low", "time": "2-4 hours", "data_migration": True},
        ("convex", "supabase"): {"complexity": "medium", "time": "6-8 hours", "data_migration": True},
        ("supabase", "convex"): {"complexity": "medium", "time": "6-8 hours", "data_migration": True},
        # Deployment migrations
        ("vercel", "railway"): {"complexity": "low", "time": "2-3 hours", "data_migration": False},
        ("railway", "vercel"): {"complexity": "low", "time": "2-3 hours", "data_migration": False},
    }

    def __init__(self):
        self.migration_steps = []
        self.prerequisites = []
        self.risks = []
        self.code_snippets = {}

    def analyze_migration(self, source: str, target: str, components: list) -> dict:
        """Analyze migration requirements and complexity."""
        migration_key = (source, target)
        complexity_info = self.MIGRATION_COMPLEXITY.get(
            migration_key, {"complexity": "unknown", "time": "unknown", "data_migration": False}
        )

        source_info = self.PROVIDERS.get(source, {})
        target_info = self.PROVIDERS.get(target, {})

        return {
            "path": f"{source} → {target}",
            "complexity": complexity_info["complexity"],
            "estimated_time": complexity_info["time"],
            "requires_data_migration": complexity_info["data_migration"],
            "components": components,
            "source_type": source_info.get("type", "unknown"),
            "target_type": target_info.get("type", "unknown"),
        }

    def generate_prerequisites(self, source: str, target: str, components: list) -> list:
        """Generate prerequisite checklist."""
        prerequisites = [
            f"Backup {source} data (full export recommended)",
            f"Create {target} account and project",
            f"Install {target} CLI tools",
            "Review {target} pricing and limits",
            "Set up development environment for testing",
        ]

        if "auth" in components:
            prerequisites.extend(
                [
                    "Export user data from source provider",
                    "Document current auth flows and integrations",
                    "Plan for auth token invalidation during cutover",
                ]
            )

        if "db" in components or "database" in components:
            prerequisites.extend(
                [
                    "Export database schema and data",
                    "Analyze query patterns and compatibility",
                    "Plan for database downtime or dual-write strategy",
                ]
            )

        if "storage" in components:
            prerequisites.extend(
                [
                    "Export storage files and metadata",
                    "Calculate storage migration data volume",
                    "Plan for CDN cache invalidation",
                ]
            )

        return prerequisites

    def generate_migration_steps(self, source: str, target: str, components: list) -> list:
        """Generate detailed migration steps."""
        steps = []
        step_num = 1

        # Common initial steps
        steps.append(
            {
                "step": step_num,
                "phase": "Preparation",
                "description": f"Set up {target} project and configure basic settings",
                "commands": [f"{target} init", f"{target} login"],
                "code_snippet": f"# Initialize {target} project\n# Follow CLI prompts for configuration",
            }
        )
        step_num += 1

        # Component-specific steps
        if "auth" in components:
            steps.extend(self._generate_auth_migration_steps(source, target, step_num))
            step_num += len(steps)

        if "db" in components or "database" in components:
            steps.extend(self._generate_database_migration_steps(source, target, step_num))
            step_num += len(steps)

        if "storage" in components:
            steps.extend(self._generate_storage_migration_steps(source, target, step_num))
            step_num += len(steps)

        # Final steps
        steps.append(
            {
                "step": step_num,
                "phase": "Testing",
                "description": "Validate migration and test all functionality",
                "commands": ["run integration tests", "verify data integrity"],
                "code_snippet": "# Run comprehensive test suite\n# Verify all migrated data",
            }
        )

        steps.append(
            {
                "step": step_num + 1,
                "phase": "Cutover",
                "description": f"Switch production traffic to {target}",
                "commands": ["update DNS/environment variables", "monitor metrics"],
                "code_snippet": f"# Update production config to point to {target}\n# Monitor error rates and performance",
            }
        )

        return steps

    def _generate_auth_migration_steps(self, source: str, target: str, start_step: int) -> list:
        """Generate authentication migration steps."""
        steps = []

        if source == "firebase_auth" and target == "supabase":
            steps.append(
                {
                    "step": start_step,
                    "phase": "Auth Migration",
                    "description": "Export Firebase Auth users and import to Supabase",
                    "commands": ["firebase auth:export users.json", "supabase db seed"],
                    "code_snippet": """-- Supabase user import SQL
INSERT INTO auth.users (id, email, encrypted_password, email_confirmed_at)
SELECT
  uid,
  email,
  password_hash,
  CURRENT_TIMESTAMP
FROM firebase_users_export;""",
                }
            )

        elif source == "auth0" and target == "clerk":
            steps.append(
                {
                    "step": start_step,
                    "phase": "Auth Migration",
                    "description": "Export Auth0 users via Management API and bulk import to Clerk",
                    "commands": ["auth0 users export", "clerk users import"],
                    "code_snippet": """// Clerk bulk import
import { Clerk } from '@clerk/clerk-sdk-node';

const clerk = Clerk({ apiKey: process.env.CLERK_API_KEY });
await clerk.users.createBulk(auth0Users);""",
                }
            )

        else:
            steps.append(
                {
                    "step": start_step,
                    "phase": "Auth Migration",
                    "description": f"Migrate users from {source} to {target}",
                    "commands": [f"{source} export", f"{target} import"],
                    "code_snippet": f"# Export from {source} and import to {target}\n# Follow provider-specific documentation",
                }
            )

        return steps

    def _generate_database_migration_steps(self, source: str, target: str, start_step: int) -> list:
        """Generate database migration steps."""
        steps = []

        if source == "firestore" and target in ["supabase", "neon"]:
            steps.append(
                {
                    "step": start_step,
                    "phase": "Schema Migration",
                    "description": "Convert Firestore NoSQL schema to PostgreSQL relational schema",
                    "commands": ["firestore export", "design postgres schema", "create migration"],
                    "code_snippet": """-- PostgreSQL schema design
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Firestore collection → PostgreSQL table mapping
-- Plan for nested documents and subcollections""",
                }
            )

            steps.append(
                {
                    "step": start_step + 1,
                    "phase": "Data Migration",
                    "description": "Transform and load Firestore data into PostgreSQL",
                    "commands": ["run ETL script", "validate data"],
                    "code_snippet": """// Data transformation script
const firestoreData = await exportFirestore();
const pgData = transformToRelational(firestoreData);
await bulkInsertPostgres(pgData);""",
                }
            )

        elif source in ["supabase", "neon"] and target in ["supabase", "neon"]:
            steps.append(
                {
                    "step": start_step,
                    "phase": "Database Copy",
                    "description": f"Dump PostgreSQL database from {source} and restore to {target}",
                    "commands": ["pg_dump", "pg_restore"],
                    "code_snippet": f"""# Export from {source}
pg_dump -h {source}.db.com -U user dbname > dump.sql

# Import to {target}
psql -h {target}.db.com -U user dbname < dump.sql""",
                }
            )

        else:
            steps.append(
                {
                    "step": start_step,
                    "phase": "Database Migration",
                    "description": f"Migrate database from {source} to {target}",
                    "commands": [f"{source} export", f"{target} import"],
                    "code_snippet": f"# Database migration script\n# Consult provider documentation",
                }
            )

        return steps

    def _generate_storage_migration_steps(self, source: str, target: str, start_step: int) -> list:
        """Generate storage migration steps."""
        return [
            {
                "step": start_step,
                "phase": "Storage Migration",
                "description": f"Copy storage files from {source} to {target}",
                "commands": [f"{source} storage export", f"{target} storage upload"],
                "code_snippet": f"""// Storage migration script
const files = await {source}.storage.listAll();
for (const file of files) {{
  const data = await {source}.storage.download(file);
  await {target}.storage.upload(file.path, data);
}}""",
            }
        ]

    def generate_risks(self, source: str, target: str, components: list) -> list:
        """Identify migration risks."""
        risks = []

        # Common risks
        risks.append("Downtime during cutover (plan for maintenance window)")
        risks.append("Data loss if migration fails (ensure comprehensive backups)")

        # Component-specific risks
        if "auth" in components:
            risks.extend(
                [
                    "Auth token invalidation (users forced to re-login)",
                    "OAuth callback URL changes (update external services)",
                    "Password hash compatibility (may require password reset)",
                ]
            )

        if "db" in components or "database" in components:
            risks.extend(
                [
                    "Query performance differences (test and optimize)",
                    "Schema incompatibilities (validate data types)",
                    "Transaction semantics differences (review critical flows)",
                ]
            )

        # Provider-specific risks
        if source == "firestore" and target in ["supabase", "neon"]:
            risks.append("NoSQL to SQL paradigm shift (major query rewrites)")

        return risks

    def generate_rollback_plan(self, source: str, target: str) -> str:
        """Generate rollback strategy."""
        return f"""Keep {source} active for 30 days post-migration:
1. Maintain {source} subscription during validation period
2. Set up monitoring on both systems
3. Keep dual-write capability if possible
4. Document rollback procedure
5. Test rollback in staging environment
6. Prepare communication plan for users if rollback needed"""


@click.command()
@click.option("--from", "source", required=True, help="Source provider (e.g., firebase, auth0)")
@click.option("--to", "target", required=True, help="Target provider (e.g., supabase, clerk)")
@click.option(
    "--components",
    multiple=True,
    type=click.Choice(["auth", "db", "database", "storage"]),
    help="Components to migrate",
)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def main(source, target, components, json_output):
    """BaaS Migration Helper - Generate migration plans and scripts."""

    # Normalize provider names
    source = source.lower().replace("-", "_")
    target = target.lower().replace("-", "_")
    components = list(components) if components else ["auth", "db"]

    # Initialize helper
    helper = BaaSMigrationHelper()

    # Analyze migration
    analysis = helper.analyze_migration(source, target, components)
    prerequisites = helper.generate_prerequisites(source, target, components)
    steps = helper.generate_migration_steps(source, target, components)
    risks = helper.generate_risks(source, target, components)
    rollback_plan = helper.generate_rollback_plan(source, target)

    # Output results
    if json_output:
        output = {
            "migration_path": analysis["path"],
            "complexity": analysis["complexity"],
            "estimated_time": analysis["estimated_time"],
            "prerequisites": prerequisites,
            "steps": steps,
            "risks": risks,
            "rollback_plan": rollback_plan,
        }
        click.echo(json.dumps(output, indent=2))
    else:
        # Human-readable output
        click.echo(f"\n🔄 BaaS Migration Plan: {analysis['path']}\n")
        click.echo(f"⚡ Complexity: {analysis['complexity'].upper()}")
        click.echo(f"⏱️  Estimated Time: {analysis['estimated_time']}")
        click.echo(f"📦 Components: {', '.join(components)}\n")

        click.echo("📋 Prerequisites:")
        for i, prereq in enumerate(prerequisites, 1):
            click.echo(f"  {i}. {prereq}")
        click.echo()

        click.echo("🛠️  Migration Steps:\n")
        for step in steps:
            click.echo(f"Step {step['step']}: {step['phase']}")
            click.echo(f"  {step['description']}")
            click.echo(f"  Commands: {', '.join(step['commands'])}")
            if step.get("code_snippet"):
                click.echo(f"  Code:\n{step['code_snippet']}")
            click.echo()

        click.echo("⚠️  Risks:")
        for i, risk in enumerate(risks, 1):
            click.echo(f"  {i}. {risk}")
        click.echo()

        click.echo("🔙 Rollback Plan:")
        click.echo(f"  {rollback_plan}\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
