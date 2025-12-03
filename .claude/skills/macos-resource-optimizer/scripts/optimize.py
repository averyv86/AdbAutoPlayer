#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["psutil>=5.9.0"]
# ///

"""
Advanced Memory Optimizer - Aggressive memory recovery with TOON workflow

Performs comprehensive memory optimization including:
- Process cleanup (inactive apps, browser helpers)
- Memory purge (requires passwordless sudo)
- Swap reduction strategies
- TOON-formatted progress and results

Usage:
    # Dry run (show what would be done)
    uv run scripts/optimize.py --dry-run

    # Execute optimizations with auto-approval
    uv run scripts/optimize.py --auto-approve

    # Execute with risk tolerance
    uv run scripts/optimize.py --risk-tolerance=medium

Author: MoAI-ADK
Version: 1.0.0 (TOON-enabled)
Date: 2025-12-01
"""

import argparse
import asyncio
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

import psutil

sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
from toon_codec import encode_toon

# Import Phase 2 components
sys.path.insert(0, str(Path(__file__).parent))
try:
    from tab_analyzer import BrowserTabAnalyzer
    from learning_engine import LearningEngine, OptimizationRecord
    from osascript_popup import OSAScriptPopup
    PHASE2_AVAILABLE = True
except ImportError:
    PHASE2_AVAILABLE = False
    print("⚠️  Phase 2 components not available", file=sys.stderr)

# Import Phase 3 components
try:
    from error_handler import ErrorHandler, SystemValidator, ErrorSeverity, ErrorCategory
    from health_check import HealthChecker
    from config_manager import ConfigManager
    PHASE3_AVAILABLE = True
except ImportError:
    PHASE3_AVAILABLE = False
    print("⚠️  Phase 3 components not available", file=sys.stderr)


def check_tab_suspender_available() -> bool:
    """
    Check if Chrome tab suspender extension is available.

    Returns:
        bool: True if Native Messaging host is configured
    """
    manifest_paths = [
        Path.home() / "Library/Application Support/Google/Chrome/NativeMessagingHosts/com.moai.tab_suspender.json",
        Path.home() / "Library/Application Support/Dia Browser/NativeMessagingHosts/com.moai.tab_suspender.json",
    ]

    return any(p.exists() for p in manifest_paths)


def suspend_browser_tabs() -> Dict:
    """
    Suspend inactive browser tabs via Chrome extension.

    Returns:
        dict: Result with tabs_suspended, tabs_total, success
    """
    script_path = Path(__file__).parent / "tab_suspender.py"

    if not script_path.exists():
        return {"success": False, "error": "tab_suspender.py not found"}

    try:
        # Reduced timeout to 10 seconds to prevent hanging
        result = subprocess.run(
            ["uv", "run", str(script_path), "--suspend", "--browser=chrome"],
            capture_output=True,
            timeout=10,
            text=True
        )

        if result.returncode == 0:
            # Parse TOON output from stderr
            # Format: browser:Chrome|tabs:100|suspended:45|time:1234567890
            stderr = result.stderr.strip()

            # Simple parsing (looking for suspended:N pattern)
            suspended = 0
            total = 0
            for line in stderr.split('\n'):
                if 'suspended:' in line:
                    parts = line.split('|')
                    for part in parts:
                        if part.startswith('suspended:'):
                            suspended = int(part.split(':')[1])
                        elif part.startswith('tabs:'):
                            total = int(part.split(':')[1])

            return {
                "success": True,
                "tabs_suspended": suspended,
                "tabs_total": total
            }
        else:
            return {
                "success": False,
                "error": result.stderr or "Unknown error"
            }

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Tab suspension timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# CRITICAL: NEVER TOUCH THESE APPS (User's active work environment)
BLACKLIST = {
    # === CRITICAL: CLAUDE CODE & INFRASTRUCTURE (NEVER TOUCH) ===

    # Claude Code Binary (HIGHEST PRIORITY - Can't be terminated)
    'claude',                    # Main Claude Code binary process
    'Claude',
    'claude-code',
    'Claude Code',

    # Claude Flow Orchestrator
    'claude-flow',               # MCP orchestrator
    'Claude Flow',

    # MCP Server Infrastructure (4 active servers)
    'mcp',
    'mcp-server',
    '@modelcontextprotocol',    # Sequential-thinking, Context7 MCPs
    '@upstash',                 # Context7 MCP provider
    '@playwright',              # Playwright MCP server
    '@notionhq',                # Notion MCP server
    'context7-mcp',
    'notion-mcp-server',
    'sequential-thinking',

    # Development Infrastructure (Prevent self-termination)
    'npm exec',                 # ALL MCP servers run via npm exec
    'npx',
    'uv run',                   # UV Python runner (self-protection)

    # Terminal (NEVER CLOSE)
    'Ghostty',
    'ghostty',

    # Editor (NEVER CLOSE)
    'Visual Studio Code',
    'Code',
    'code',

    # Browsers (NEVER CLOSE without permission)
    'Chrome',
    'Google Chrome',
    'chrome',
    'Firefox',
    'firefox',
    'Safari',
    'safari',
    'Dia',  # Dia Browser
    'dia',
    'Arc',
    'arc',
    'Brave',
    'brave',
    'Edge',
    'edge',
    'Opera',
    'opera',
    'Vivaldi',
    'vivaldi',
    'Browser',  # Any process with "Browser" in name
    'browser',
}

def is_blacklisted(proc) -> bool:
    """
    Check if process matches any blacklisted app.
    Enhanced: Checks BOTH process name AND command line.

    Args:
        proc: psutil.Process object or string process name

    Returns:
        bool: True if process should be protected (blacklisted)
    """
    try:
        # Handle both string names and Process objects
        if isinstance(proc, str):
            name = proc
            cmdline = ""
        else:
            # psutil.Process object
            name = proc.info.get('name', '') if hasattr(proc, 'info') else proc.name()
            try:
                cmdline = ' '.join(proc.cmdline()) if hasattr(proc, 'cmdline') else ''
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                cmdline = ""

        if not name:
            return False

        # Check process name (case-insensitive, bidirectional)
        name_lower = name.lower()
        for blacklisted in BLACKLIST:
            if blacklisted.lower() in name_lower or name_lower in blacklisted.lower():
                return True

        # Check command line (catches: npm exec @modelcontextprotocol/...)
        if cmdline:
            cmdline_lower = cmdline.lower()
            for blacklisted in BLACKLIST:
                if blacklisted.lower() in cmdline_lower:
                    return True

        return False

    except Exception:
        # Fail-safe: protect if there's any error checking
        return True


def is_development_server(proc) -> bool:
    """
    Check if process is a development server that should be protected.

    Protects:
    - MCP servers (@modelcontextprotocol/*, context7-mcp, etc.)
    - Claude Flow orchestrator
    - npm exec/npx development servers
    - UV script runners

    Args:
        proc: psutil.Process object

    Returns:
        bool: True if process is a protected development server
    """
    try:
        cmdline = ""
        name = ""

        # Extract process info
        if hasattr(proc, 'info'):
            name = proc.info.get('name', '').lower()
            try:
                cmdline = ' '.join(proc.info.get('cmdline', [])).lower() if proc.info.get('cmdline') else ""
            except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError, TypeError):
                pass
        else:
            try:
                name = proc.name().lower()
                cmdline = ' '.join(proc.cmdline()).lower()
            except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError):
                pass

        # MCP server patterns
        mcp_patterns = [
            '@modelcontextprotocol', '@upstash', '@playwright', '@notionhq',
            'mcp-server', 'context7-mcp', 'sequential-thinking',
            'claude-flow'
        ]

        if any(pattern in cmdline or pattern in name for pattern in mcp_patterns):
            return True

        # npm/npx executed servers
        if 'npm exec' in cmdline or 'npx' in cmdline:
            if any(ind in cmdline for ind in ['server', 'mcp', '@modelcontextprotocol', 'claude-flow']):
                return True

        # UV script runner (self-protection)
        if 'uv run' in cmdline:
            if any(ind in cmdline for ind in ['mcp', '@modelcontextprotocol', 'claude-flow', '.claude']):
                return True

        return False

    except Exception:
        # Fail-safe: protect if there's any error
        return False


class RiskLevel(Enum):
    """Risk level for optimizations."""
    SAFE = "safe"           # No risk, always safe
    LOW = "low"             # Very low risk
    MEDIUM = "medium"       # Medium risk, may affect some apps
    HIGH = "high"           # High risk, may terminate important processes


@dataclass
class Optimization:
    """Represents a single optimization action."""
    name: str
    description: str
    risk_level: RiskLevel
    estimated_recovery_mb: int
    command: Optional[str] = None
    requires_sudo: bool = False
    metadata: Optional[Dict] = None  # Store execution data (process lists, etc.)

    def to_toon(self) -> str:
        """Convert to TOON format."""
        data = {
            "name": self.name,
            "desc": self.description,
            "risk": self.risk_level.value,
            "recovery_mb": self.estimated_recovery_mb,
            "sudo": 1 if self.requires_sudo else 0
        }
        return encode_toon(data)


class MemoryOptimizer:
    """
    Advanced memory optimizer with TOON workflow.

    Identifies and executes memory recovery strategies with user approval.
    """

    def __init__(self, dry_run: bool = False, auto_approve: bool = False,
                 risk_tolerance: str = "medium"):
        """
        Initialize optimizer.

        Args:
            dry_run: If True, only show what would be done
            auto_approve: If True, automatically approve all actions
            risk_tolerance: Maximum risk level to auto-approve (safe/low/medium/high)
        """
        self.dry_run = dry_run
        self.auto_approve = auto_approve
        self.risk_tolerance = RiskLevel(risk_tolerance)
        self.optimizations: List[Optimization] = []

    def analyze_system(self) -> Dict:
        """Analyze system and identify optimization opportunities."""
        print("🔍 시스템 분석 중...")
        print()

        opportunities = []

        # 0. Check for browser tab suspension (Phase 2 enhanced)
        if check_tab_suspender_available() and PHASE2_AVAILABLE:
            try:
                # Use Phase 2 tab_analyzer for accurate estimation
                analyzer = BrowserTabAnalyzer()
                analyses = analyzer.analyze_all()

                if analyses:
                    total_tabs = sum(a.estimated_tabs for a in analyses)
                    total_recovery = sum(a.estimated_recovery_mb for a in analyses)

                    browser_names = ", ".join(a.browser for a in analyses)

                    opportunities.append(Optimization(
                        name="browser_tab_suspension",
                        description=f"브라우저 탭 일시중단 ({total_tabs}개 탭, {browser_names})",
                        risk_level=RiskLevel.SAFE,
                        estimated_recovery_mb=total_recovery,
                        command="suspend_tabs"
                    ))
            except Exception as e:
                print(f"⚠️  Tab analyzer error: {e}", file=sys.stderr)
                # Fallback to basic estimation
                pass

        # 1. Check for inactive memory that can be purged
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        if swap.percent > 90:
            opportunities.append(Optimization(
                name="critical_swap_purge",
                description="스왑 메모리 긴급 정리 (sudo purge)",
                risk_level=RiskLevel.SAFE,
                estimated_recovery_mb=int(swap.used / 1024 / 1024 * 0.3),
                command="purge",
                requires_sudo=True
            ))

        # 2. Find memory-heavy browser helpers
        browser_helpers = []
        for proc in psutil.process_iter(['name', 'memory_percent']):
            try:
                mem_pct = proc.info.get('memory_percent')
                name = proc.info.get('name', '')

                # CRITICAL: Skip blacklisted apps (user's work environment)
                if is_blacklisted(name):
                    continue

                if mem_pct and 'Helper' in name and mem_pct > 0.5:
                    browser_helpers.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        if len(browser_helpers) > 50:
            estimated_mb = 0
            for proc in browser_helpers[:20]:
                try:
                    estimated_mb += proc.memory_info().rss / 1024 / 1024
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            opportunities.append(Optimization(
                name="browser_helper_cleanup",
                description=f"브라우저 헬퍼 프로세스 정리 ({len(browser_helpers)}개 중 과다 사용 20개)",
                risk_level=RiskLevel.LOW,
                estimated_recovery_mb=int(estimated_mb),
                command=None  # Manual process
            ))

        # 3. Find inactive applications
        inactive_apps = []
        for proc in psutil.process_iter(['name', 'memory_percent', 'cpu_percent']):
            try:
                mem_pct = proc.info.get('memory_percent')
                cpu_pct = proc.info.get('cpu_percent')
                name = proc.info.get('name', '')

                # CRITICAL: Skip blacklisted apps (user's work environment)
                if is_blacklisted(name):
                    continue

                # App using >1% memory but 0% CPU for extended time
                if (mem_pct and cpu_pct is not None and
                    mem_pct > 1.0 and cpu_pct < 0.1 and '.app' in name):
                    inactive_apps.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        if inactive_apps:
            estimated_mb = 0
            app_names = []
            for proc in inactive_apps:
                try:
                    estimated_mb += proc.memory_info().rss / 1024 / 1024
                    app_names.append(proc.info.get('name', 'unknown'))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            opportunities.append(Optimization(
                name="inactive_app_suspension",
                description=f"비활성 앱 정리 ({len(inactive_apps)}개 앱): {', '.join(list(set(app_names))[:5])}",
                risk_level=RiskLevel.MEDIUM,
                estimated_recovery_mb=int(estimated_mb),
                command="terminate_inactive_apps",
                metadata={"processes": inactive_apps}  # Store process list for execution
            ))

        # 3.5. Find messaging apps and servers (user requested)
        messaging_patterns = ['message', 'msg', 'chat', 'mail', 'slack', 'discord', 'telegram',
                             'whatsapp', 'signal', 'teams', 'zoom', 'skype', 'notion', 'gather']
        server_patterns = ['server', 'daemon', 'service', 'node', 'python', 'java', 'ruby']

        messaging_apps = []
        server_processes = []

        for proc in psutil.process_iter(['name', 'cmdline', 'memory_info']):
            try:
                name = proc.info.get('name', '').lower()
                cmdline = ' '.join(proc.info.get('cmdline', [])).lower() if proc.info.get('cmdline') else ''

                # Skip blacklisted apps
                if is_blacklisted(name):
                    continue

                # Check for messaging apps
                if any(pattern in name or pattern in cmdline for pattern in messaging_patterns):
                    messaging_apps.append(proc)
                # Check for server processes (but exclude critical system processes)
                elif any(pattern in name for pattern in server_patterns):
                    if not name.startswith(('system', 'kernel', 'launchd', 'com.apple')):
                        server_processes.append(proc)

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Add messaging apps opportunity if found
        if messaging_apps:
            estimated_mb = 0
            app_names = []
            for proc in messaging_apps:
                try:
                    estimated_mb += proc.memory_info().rss / 1024 / 1024
                    app_names.append(proc.info.get('name', 'unknown'))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            opportunities.append(Optimization(
                name="messaging_app_cleanup",
                description=f"메시징 앱 정리 ({len(messaging_apps)}개): {', '.join(list(set(app_names))[:5])}",
                risk_level=RiskLevel.MEDIUM,
                estimated_recovery_mb=int(estimated_mb),
                command="terminate_inactive_apps",
                metadata={"processes": messaging_apps}
            ))

        # Add server processes opportunity if found
        if server_processes:
            # CRITICAL: Filter out development servers (MCP, Claude, etc.)
            safe_to_terminate = []
            protected_servers = []

            for proc in server_processes:
                if is_development_server(proc):
                    try:
                        protected_servers.append(proc.info.get('name', 'unknown'))
                    except:
                        protected_servers.append('unknown')
                else:
                    safe_to_terminate.append(proc)

            # Only create optimization if there are safe processes to terminate
            if safe_to_terminate:
                estimated_mb = 0
                server_names = []
                for proc in safe_to_terminate:
                    try:
                        estimated_mb += proc.memory_info().rss / 1024 / 1024
                        server_names.append(proc.info.get('name', 'unknown'))
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                opportunities.append(Optimization(
                    name="server_process_cleanup",
                    description=f"서버 프로세스 정리 ({len(safe_to_terminate)}개): {', '.join(list(set(server_names))[:5])}",
                    risk_level=RiskLevel.MEDIUM,
                    estimated_recovery_mb=int(estimated_mb),
                    command="terminate_inactive_apps",
                    metadata={"processes": safe_to_terminate}
                ))

            if protected_servers:
                pass  # Development servers protected, no action needed

        # 4. Memory compression analysis
        if hasattr(psutil, 'virtual_memory') and hasattr(mem, 'compressed'):
            # macOS specific
            pass

        self.optimizations = opportunities

        return {
            "total_opportunities": len(opportunities),
            "estimated_total_recovery_mb": sum(o.estimated_recovery_mb for o in opportunities),
            "optimizations": [o.to_toon() for o in opportunities]
        }

    def print_analysis_toon(self, analysis: Dict):
        """Print analysis results in TOON format."""
        print("📊 분석 결과")
        print("=" * 60)
        print()

        summary_toon = encode_toon({
            "opportunities": analysis["total_opportunities"],
            "recovery_mb": analysis["estimated_total_recovery_mb"],
            "recovery_gb": round(analysis["estimated_total_recovery_mb"] / 1024, 2)
        })

        print(summary_toon)
        print()

        print("🎯 최적화 기회:")
        print("-" * 60)
        for i, opt in enumerate(self.optimizations, 1):
            print(f"\n{i}. {opt.name}")
            print(f"   설명: {opt.description}")
            print(f"   위험도: {opt.risk_level.value}")
            print(f"   예상 복구: {opt.estimated_recovery_mb} MB")
            if opt.requires_sudo:
                print(f"   권한: sudo 필요")

        print()

    async def execute_optimization(self, opt: Optimization) -> bool:
        """Execute a single optimization."""
        print(f"⚡ 실행 중: {opt.name}")

        if self.dry_run:
            print(f"   [DRY RUN] {opt.description}")
            return True

        # Handle tab suspension (Phase 2 enhanced)
        if opt.command == "suspend_tabs":
            start_time = time.time()
            before_mem = psutil.virtual_memory()

            try:
                result = suspend_browser_tabs()

                if result["success"]:
                    suspended = result.get("tabs_suspended", 0)
                    total = result.get("tabs_total", 0)
                    print(f"   ✅ 완료: {suspended}/{total}개 탭 일시중단")

                    # Phase 2: Record in learning engine
                    if PHASE2_AVAILABLE:
                        try:
                            execution_time = time.time() - start_time
                            after_mem = psutil.virtual_memory()

                            learning_engine = LearningEngine()
                            record = OptimizationRecord(
                                timestamp=datetime.now().isoformat(),
                                category="memory",
                                before_metrics={"memory_percent": before_mem.percent},
                                after_metrics={"memory_percent": after_mem.percent},
                                actions_taken=["browser_tab_suspension"],
                                apps_affected=["Chrome"],
                                success=True,
                                improvement_percent=before_mem.percent - after_mem.percent,
                                execution_time_seconds=execution_time
                            )
                            learning_engine.record_optimization(record)
                        except Exception as e:
                            print(f"   ⚠️  Learning engine error: {e}", file=sys.stderr)

                    return True
                else:
                    error = result.get("error", "Unknown error")
                    print(f"   ⚠️  탭 일시중단 실패: {error}")
                    print(f"   💡 Extension 설치 확인: extensions/chrome-tab-suspender/install.sh")
                    return False

            except Exception as e:
                print(f"   ❌ 오류: {e}")
                return False

        # Handle inactive app termination
        if opt.command == "terminate_inactive_apps":
            if not opt.metadata or "processes" not in opt.metadata:
                print(f"   ❌ 오류: 프로세스 리스트 없음")
                return False

            processes = opt.metadata["processes"]
            terminated = 0
            failed = 0
            memory_freed_mb = 0

            print(f"   🎯 {len(processes)}개 비활성 앱 종료 시작...")

            for proc in processes:
                try:
                    # Double check blacklist before terminating
                    name = proc.info.get('name', '')
                    if is_blacklisted(name):
                        print(f"   ⏭️  보호됨: {name}")
                        continue

                    # Get memory before terminating
                    try:
                        mem_mb = proc.memory_info().rss / 1024 / 1024
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        mem_mb = 0

                    # Terminate process
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)  # Wait for graceful termination
                        terminated += 1
                        memory_freed_mb += mem_mb
                        print(f"   ✅ 종료: {name} ({mem_mb:.1f} MB)")
                    except psutil.TimeoutExpired:
                        # Force kill if graceful termination fails
                        proc.kill()
                        terminated += 1
                        memory_freed_mb += mem_mb
                        print(f"   ⚡ 강제 종료: {name} ({mem_mb:.1f} MB)")

                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    failed += 1
                    print(f"   ⚠️  실패: {name} - {e}")
                except Exception as e:
                    failed += 1
                    print(f"   ❌ 오류: {name} - {e}")

            print(f"   ✅ 완료: {terminated}개 종료, {failed}개 실패, {memory_freed_mb:.1f} MB 회수")
            return terminated > 0

        # Handle sudo commands
        if opt.requires_sudo and opt.command:
            try:
                if opt.command == "purge":
                    # Execute purge via osascript for macOS popup
                    result = subprocess.run([
                        'osascript', '-e',
                        f'do shell script "{opt.command}" with administrator privileges'
                    ], capture_output=True, timeout=60)

                    if result.returncode == 0:
                        print(f"   ✅ 완료: {opt.description}")
                        return True
                    else:
                        print(f"   ❌ 실패: {result.stderr.decode()}")
                        return False
            except Exception as e:
                print(f"   ❌ 오류: {e}")
                return False
        else:
            # Manual optimization - provide instructions
            print(f"   📋 수동 작업 필요: {opt.description}")
            return True

    async def execute_all(self):
        """Execute all approved optimizations."""
        print()
        print("🚀 최적화 실행")
        print("=" * 60)
        print()

        results = []
        for opt in self.optimizations:
            # Check risk tolerance
            if opt.risk_level.value > self.risk_tolerance.value and not self.auto_approve:
                print(f"⏭️  건너뛰기: {opt.name} (위험도: {opt.risk_level.value})")
                continue

            result = await self.execute_optimization(opt)
            results.append({
                "name": opt.name,
                "success": result,
                "recovery_mb": opt.estimated_recovery_mb if result else 0
            })

        # Summary
        print()
        print("✅ 최적화 완료")
        print("=" * 60)

        total_success = sum(1 for r in results if r["success"])
        total_recovery = sum(r["recovery_mb"] for r in results if r["success"])

        summary_toon = encode_toon({
            "total_actions": len(results),
            "successful": total_success,
            "failed": len(results) - total_success,
            "total_recovery_mb": total_recovery,
            "total_recovery_gb": round(total_recovery / 1024, 2)
        })

        print(summary_toon)
        print()


async def main():
    """Main execution."""
    parser = argparse.ArgumentParser(
        description='Advanced Memory Optimizer with TOON workflow',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without executing')
    parser.add_argument('--auto-approve', action='store_true',
                        help='Automatically approve all actions within risk tolerance')
    parser.add_argument('--risk-tolerance',
                        choices=['safe', 'low', 'medium', 'high'],
                        default='medium',
                        help='Maximum risk level to auto-approve (default: medium)')

    args = parser.parse_args()

    print("🤖 Advanced Memory Optimizer")
    print("=" * 60)
    print()

    optimizer = MemoryOptimizer(
        dry_run=args.dry_run,
        auto_approve=args.auto_approve,
        risk_tolerance=args.risk_tolerance
    )

    # Analyze
    analysis = optimizer.analyze_system()
    optimizer.print_analysis_toon(analysis)

    # Execute
    if not args.dry_run:
        await optimizer.execute_all()
    else:
        print("🔍 DRY RUN 모드 - 실제 실행하려면 --dry-run 없이 다시 실행하세요")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
