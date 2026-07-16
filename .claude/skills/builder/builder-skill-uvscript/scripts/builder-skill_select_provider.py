#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "click>=8.0.0",
# ]
# ///
"""
BaaS Provider Selection Tool

Interactive BaaS provider selection based on user requirements.
Analyzes requirements against 9 providers and recommends optimal stack.

Usage:
    uv run provider_selector.py --auth oauth --database postgres --hosting serverless --budget hobby
    uv run provider_selector.py --auth jwt --database realtime --json
"""

import json
import sys
from pathlib import Path
from typing import Any

import click


class BaaSProviderSelector:
    """AI-powered BaaS provider selection engine."""

    PROVIDERS = {
        "auth": {
            "auth0": {
                "strengths": ["enterprise_sso", "50_connections", "b2b_saas", "rbac"],
                "cost_tier": "enterprise",
                "supports": ["oauth", "jwt", "session"],
                "score_weights": {"oauth": 3.0, "jwt": 2.5, "session": 2.0},
            },
            "clerk": {
                "strengths": ["webauthn", "passkey", "modern_ui", "organizations"],
                "cost_tier": "mid_tier",
                "supports": ["oauth", "jwt", "passkey", "session"],
                "score_weights": {"passkey": 3.0, "oauth": 2.5, "jwt": 2.0, "session": 2.0},
            },
            "firebase_auth": {
                "strengths": ["google_integration", "mobile_first", "analytics"],
                "cost_tier": "pay_as_you_go",
                "supports": ["oauth", "jwt", "session"],
                "score_weights": {"oauth": 2.5, "jwt": 2.0, "session": 2.0},
            },
        },
        "database": {
            "supabase": {
                "strengths": ["postgres_16", "realtime", "rls", "pgvector"],
                "cost_tier": "mid_tier",
                "supports": ["postgres", "realtime"],
                "score_weights": {"postgres": 3.0, "realtime": 3.0},
            },
            "neon": {
                "strengths": ["serverless", "auto_scaling", "branching", "pitr_30days"],
                "cost_tier": "pay_as_you_go",
                "supports": ["postgres"],
                "score_weights": {"postgres": 3.0},
            },
            "convex": {
                "strengths": ["realtime_backend", "reactive", "optimistic_updates", "typescript"],
                "cost_tier": "mid_tier",
                "supports": ["realtime"],
                "score_weights": {"realtime": 3.0},
            },
            "firestore": {
                "strengths": ["mobile_sync", "offline_support", "google_integration"],
                "cost_tier": "pay_as_you_go",
                "supports": ["firestore", "realtime"],
                "score_weights": {"firestore": 3.0, "realtime": 2.5},
            },
        },
        "deployment": {
            "vercel": {
                "strengths": ["edge_deployment", "nextjs_optimization", "global_cdn", "zero_config"],
                "cost_tier": "mid_tier",
                "supports": ["serverless", "static"],
                "score_weights": {"serverless": 3.0, "static": 3.0},
            },
            "railway": {
                "strengths": ["containers", "full_stack", "multi_region", "docker"],
                "cost_tier": "mid_tier",
                "supports": ["containers", "serverless"],
                "score_weights": {"containers": 3.0, "serverless": 2.0},
            },
        },
    }

    BUDGET_TIERS = {
        "free": {"limit": 0, "weight": 1.0, "recommended": ["firebase_auth", "firestore", "vercel"]},
        "hobby": {"limit": 100, "weight": 0.8, "recommended": ["clerk", "neon", "vercel"]},
        "professional": {"limit": 500, "weight": 0.5, "recommended": ["clerk", "supabase", "vercel"]},
        "enterprise": {"limit": 1000, "weight": 0.2, "recommended": ["auth0", "supabase", "railway"]},
    }

    def __init__(self):
        self.results = {"auth": {}, "database": {}, "deployment": {}}

    def score_provider(
        self, category: str, provider: str, config: dict, user_requirements: dict
    ) -> tuple[float, list[str]]:
        """Score a provider based on requirements."""
        score = 0.0
        rationale = []

        # Requirement match scoring
        if user_requirements.get(category):
            req = user_requirements[category]
            if req in config["supports"]:
                match_score = config["score_weights"].get(req, 1.0)
                score += match_score
                rationale.append(f"Supports {req} authentication" if category == "auth" else f"Supports {req}")

        # Budget tier scoring
        budget = user_requirements.get("budget", "hobby")
        tier_info = self.BUDGET_TIERS[budget]
        if provider in tier_info["recommended"]:
            budget_score = tier_info["weight"] * 2.0
            score += budget_score
            rationale.append(f"Recommended for {budget} tier")

        # Hosting preference scoring (deployment only)
        if category == "deployment" and user_requirements.get("hosting"):
            hosting = user_requirements["hosting"]
            if hosting in config["supports"]:
                hosting_score = config["score_weights"].get(hosting, 1.5)
                score += hosting_score
                rationale.append(f"Optimized for {hosting} hosting")

        # Special combinations
        if category == "database" and user_requirements.get("database") == "postgres":
            if provider in ["supabase", "neon"]:
                score += 1.0
                rationale.append("Native PostgreSQL support")

        if category == "database" and user_requirements.get("database") == "realtime":
            if provider in ["supabase", "convex", "firestore"]:
                score += 1.0
                rationale.append("Real-time features built-in")

        return score, rationale

    def select_optimal_stack(self, requirements: dict) -> dict:
        """Select optimal provider stack based on requirements."""
        recommendations = {}
        all_scores = {}

        for category, providers in self.PROVIDERS.items():
            category_scores = {}
            category_rationale = {}

            for provider, config in providers.items():
                score, rationale = self.score_provider(category, provider, config, requirements)
                category_scores[provider] = score
                category_rationale[provider] = rationale

            # Select best provider for category
            best_provider = max(category_scores, key=category_scores.get)
            recommendations[category] = best_provider
            all_scores[category] = category_scores

            # Store results
            self.results[category] = {
                "recommended": best_provider,
                "score": category_scores[best_provider],
                "rationale": category_rationale[best_provider],
                "alternatives": sorted(
                    [
                        {"name": p, "score": s, "reason": category_rationale[p][0] if category_rationale[p] else "N/A"}
                        for p, s in category_scores.items()
                        if p != best_provider
                    ],
                    key=lambda x: x["score"],
                    reverse=True,
                )[:2],
            }

        return {
            "recommended_stack": recommendations,
            "confidence": self._calculate_confidence(all_scores),
            "details": self.results,
        }

    def _calculate_confidence(self, scores: dict) -> float:
        """Calculate overall confidence score."""
        total_score = sum(max(category_scores.values()) for category_scores in scores.values())
        max_possible = len(scores) * 10.0  # Theoretical max
        return min(total_score / max_possible, 1.0)

    def estimate_cost(self, stack: dict, budget: str) -> dict:
        """Estimate monthly cost for recommended stack."""
        cost_estimates = {
            "free": {"auth": "$0", "database": "$0", "deployment": "$0", "total": "$0/month"},
            "hobby": {"auth": "$20-30", "database": "$25", "deployment": "$20", "total": "$65-75/month"},
            "professional": {"auth": "$100-150", "database": "$100", "deployment": "$100", "total": "$300-350/month"},
            "enterprise": {
                "auth": "$500+",
                "database": "$500+",
                "deployment": "$500+",
                "total": "$1500+/month",
            },
        }

        return {
            "budget_tier": budget,
            "estimated_costs": cost_estimates.get(budget, cost_estimates["hobby"]),
            "scaling_note": "Costs increase with usage beyond free/hobby tiers",
        }


@click.command()
@click.option(
    "--auth",
    type=click.Choice(["oauth", "jwt", "passkey", "session"]),
    help="Authentication type needed",
)
@click.option(
    "--database",
    type=click.Choice(["postgres", "firestore", "realtime", "none"]),
    help="Database type",
)
@click.option(
    "--hosting",
    type=click.Choice(["serverless", "containers", "static", "any"]),
    help="Hosting preference",
)
@click.option(
    "--budget",
    type=click.Choice(["free", "hobby", "professional", "enterprise"]),
    default="hobby",
    help="Budget tier",
)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def main(auth, database, hosting, budget, json_output):
    """BaaS Provider Selection Tool - AI-powered stack recommendation."""

    # Build requirements
    requirements = {"budget": budget}
    if auth:
        requirements["auth"] = auth
    if database:
        requirements["database"] = database
    if hosting:
        requirements["hosting"] = hosting

    # Select providers
    selector = BaaSProviderSelector()
    result = selector.select_optimal_stack(requirements)
    cost_estimate = selector.estimate_cost(result["recommended_stack"], budget)

    # Output results
    if json_output:
        output = {
            "recommended_stack": result["recommended_stack"],
            "confidence": round(result["confidence"], 2),
            "authentication": {
                "provider": result["details"]["auth"]["recommended"],
                "score": round(result["details"]["auth"]["score"], 2),
                "rationale": result["details"]["auth"]["rationale"],
                "alternatives": result["details"]["auth"]["alternatives"],
            },
            "database": {
                "provider": result["details"]["database"]["recommended"],
                "score": round(result["details"]["database"]["score"], 2),
                "rationale": result["details"]["database"]["rationale"],
                "alternatives": result["details"]["database"]["alternatives"],
            },
            "deployment": {
                "provider": result["details"]["deployment"]["recommended"],
                "score": round(result["details"]["deployment"]["score"], 2),
                "rationale": result["details"]["deployment"]["rationale"],
                "alternatives": result["details"]["deployment"]["alternatives"],
            },
            "cost_estimate": cost_estimate,
        }
        click.echo(json.dumps(output, indent=2))
    else:
        # Human-readable output
        click.echo("\n🎯 BaaS Provider Recommendation\n")
        click.echo(f"Confidence: {result['confidence']:.0%}\n")

        click.echo("📦 Recommended Stack:")
        click.echo(f"  Authentication: {result['recommended_stack']['auth']}")
        click.echo(f"  Database:       {result['recommended_stack']['database']}")
        click.echo(f"  Deployment:     {result['recommended_stack']['deployment']}\n")

        # Details
        for category in ["auth", "database", "deployment"]:
            details = result["details"][category]
            click.echo(f"✅ {category.title()}:")
            click.echo(f"   Provider: {details['recommended']} (score: {details['score']:.1f})")
            click.echo(f"   Rationale:")
            for reason in details["rationale"]:
                click.echo(f"     • {reason}")
            if details["alternatives"]:
                click.echo(f"   Alternatives:")
                for alt in details["alternatives"]:
                    click.echo(f"     • {alt['name']} (score: {alt['score']:.1f}) - {alt['reason']}")
            click.echo()

        # Cost estimate
        click.echo("💰 Cost Estimate:")
        click.echo(f"   Budget Tier: {cost_estimate['budget_tier']}")
        click.echo(f"   Estimated Total: {cost_estimate['estimated_costs']['total']}")
        click.echo(f"   Note: {cost_estimate['scaling_note']}\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
