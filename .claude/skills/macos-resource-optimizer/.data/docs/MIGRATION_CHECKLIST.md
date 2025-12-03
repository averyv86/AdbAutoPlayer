# Migration Checklist: v6.0 → v7.0

**macOS Resource Optimizer Migration**
**Version**: 1.0.0
**Last Updated**: 2025-11-30
**Status**: Ready for Use

---

## Overview

This checklist provides a step-by-step guide for migrating from v6.0 to v7.0. Follow each section in order. Check off items as you complete them.

**Estimated Time**: 45-60 minutes
**Risk Level**: Low
**Rollback Support**: Yes

---

## Phase 1: Pre-Migration Preparation (10 minutes)

### Verify Current Environment

- [ ] Check v6.0 version: `/macos-optimizer:analyze --version` (should show v6.0.x)
- [ ] Verify Python is installed: `python --version` (3.8+)
- [ ] Check psutil dependency: `python -c "import psutil; print(psutil.__version__)"`
- [ ] Verify git status: `git status` (no uncommitted changes on critical files)
- [ ] Check disk space: `df -h` (at least 500MB free)
- [ ] Verify network connectivity: `ping -c 1 github.com`

### Document Current State

- [ ] Get v6.0 version: `OPTIMIZER_V6=$(moai-adk info | grep version)`
- [ ] Export current config: `cp .claude/skills/macos-resource-optimizer/.data/config.yaml .claude/skills/macos-resource-optimizer/.data/config.yaml.v6.baseline`
- [ ] Run final v6.0 analysis: `/macos-optimizer:analyze > /tmp/v6_baseline_$(date +%s).json`
- [ ] List custom agents: `find .claude/skills/macos-resource-optimizer/.data/agents -name "custom_*.py" | tee /tmp/custom_agents.txt`
- [ ] Check modification dates: `ls -lt .claude/skills/macos-resource-optimizer/.data/*.py | head -10`
- [ ] Document any recent changes: `git log --oneline .claude/skills/macos-resource-optimizer/.data/ | head -20 > /tmp/recent_changes.log`

### Review Migration Guide

- [ ] Read MIGRATION_v6_to_v7.md (Overview and Breaking Changes sections)
- [ ] Review the Feature Comparison Matrix
- [ ] Understand the Architecture changes
- [ ] Note the three breaking changes (namespace, response format, config)
- [ ] Familiarize yourself with rollback procedure

---

## Phase 2: Backup Creation (5 minutes)

### Create Backup

- [ ] Create backup directory: `mkdir -p .claude/skills/macos-resource-optimizer/.data.v6.backup`
- [ ] Copy all optimizer files: `cp -r .claude/skills/macos-resource-optimizer/.data/* .claude/skills/macos-resource-optimizer/.data.v6.backup/`
- [ ] Verify backup content: `ls -la .claude/skills/macos-resource-optimizer/.data.v6.backup/` (should show same structure)
- [ ] Check backup completeness: `diff -r .claude/skills/macos-resource-optimizer/.data .claude/skills/macos-resource-optimizer/.data.v6.backup` (should show no differences)

### Archive Backup

- [ ] Create timestamped archive: `tar -czf macos-optimizer-v6-backup-$(date +%Y%m%d-%H%M%S).tar.gz .claude/skills/macos-resource-optimizer/.data.v6.backup/`
- [ ] Verify archive: `tar -tzf macos-optimizer-v6-backup-*.tar.gz | head -20`
- [ ] Calculate archive size: `du -sh macos-optimizer-v6-backup-*.tar.gz`
- [ ] Store in safe location: `mv macos-optimizer-v6-backup-*.tar.gz ~/.backups/` (optional)
- [ ] Document backup location: Record path to backup (e.g., `~/.backups/macos-optimizer-v6-backup-20251130.tar.gz`)

### Verify Backup Integrity

- [ ] Test archive extraction: `tar -tzf macos-optimizer-v6-backup-*.tar.gz > /dev/null && echo "✅ Archive valid"`
- [ ] Spot check critical files exist:
  - [ ] `.claude/skills/macos-resource-optimizer/.data/coordinator.py` in backup
  - [ ] `.claude/skills/macos-resource-optimizer/.data/config.yaml` in backup
  - [ ] `.claude/skills/macos-resource-optimizer/.data/agents/` directory in backup
  - [ ] `.claude/skills/macos-resource-optimizer/.data/tests/` directory in backup

---

## Phase 3: MoAI-ADK Update (5 minutes)

### Update Framework

- [ ] Check current MoAI-ADK version: `moai-adk --version`
- [ ] Update to latest: `moai-adk update` (requires v0.30.2+)
- [ ] Verify new version: `moai-adk --version` (confirm ≥0.30.2)
- [ ] Check update logs: `moai-adk status` (should show "up to date")

### Verify Dependencies

- [ ] Check Node.js (for MCP servers): `node --version` (v18+)
- [ ] Check npm: `npm --version`
- [ ] Check Python dependencies: `pip list | grep -E "(psutil|pytest)"`
- [ ] Install missing deps: `pip install psutil pytest pytest-asyncio` (if needed)

### Install macOS Resource Optimizer

- [ ] Install package: `moai-adk install macos-resource-optimizer`
- [ ] Verify installation: `ls -la .claude/commands/macos-resource-optimizer/`
- [ ] Check for 6 command files (0-init, 1-analyze, 2-optimize, 3-monitor, 4-report, 9-feedback)
- [ ] Verify agent files: `ls -la .claude/agents/macos-resource/`

---

## Phase 4: Configuration Migration (10 minutes)

### Convert Configuration Format

- [ ] Verify input config: `cat .claude/skills/macos-resource-optimizer/.data/config.yaml | head -20`
- [ ] Check script exists: `ls -la .claude/skills/macos-resource-optimizer/.data/scripts/migrate_config.py`
- [ ] Run conversion script: `python .claude/skills/macos-resource-optimizer/.data/scripts/migrate_config.py --input .claude/skills/macos-resource-optimizer/.data/config.yaml --output .claude/skills/macos-resource-optimizer/.data/config.json --backup`
- [ ] Verify conversion succeeded: `echo $?` (should show 0)
- [ ] Check output file: `ls -la .claude/skills/macos-resource-optimizer/.data/config.json`

### Validate New Configuration

- [ ] Validate JSON syntax: `python -m json.tool .claude/skills/macos-resource-optimizer/.data/config.json > /dev/null && echo "✅ Valid"`
- [ ] View config structure: `python -c "import json; c=json.load(open('.claude/skills/macos-resource-optimizer/.data/config.json')); print(json.dumps(c, indent=2))" | head -30`
- [ ] Check required keys: `python -c "import json; c=json.load(open('.claude/skills/macos-resource-optimizer/.data/config.json')); assert 'macos_optimizer' in c"`
- [ ] Verify caching settings: `grep -q '"cache"' .claude/skills/macos-resource-optimizer/.data/config.json && echo "✅ Cache config found"`
- [ ] Verify parallel execution: `grep -q '"parallel_execution"' .claude/skills/macos-resource-optimizer/.data/config.json && echo "✅ Parallel execution config found"`

### Compare Configurations

- [ ] Create side-by-side comparison: `echo "=== v6.0 YAML ===" && cat .claude/skills/macos-resource-optimizer/.data/config.yaml && echo -e "\n=== v7.0 JSON ===" && python -m json.tool .claude/skills/macos-resource-optimizer/.data/config.json`
- [ ] Verify no settings lost: Check all v6.0 settings appear in v7.0 config
- [ ] Review cache TTL setting: `grep "ttl_seconds" .claude/skills/macos-resource-optimizer/.data/config.json` (should show 30)
- [ ] Confirm categories list: `grep -A 5 '"categories"' .claude/skills/macos-resource-optimizer/.data/config.json`

---

## Phase 5: Initialization & Validation (10 minutes)

### Initialize v7.0

- [ ] Run init command: `/macos-resource-optimizer:0-init`
- [ ] Expected output should contain:
  - [ ] ✅ Python engine: Ready
  - [ ] ✅ MoAI wrapper: Active
  - [ ] ✅ Dependencies: Compatible
  - [ ] ✅ Migration: Check-required
- [ ] Run validation: `/macos-resource-optimizer:0-init --validate`
- [ ] Enable caching (recommended): `/macos-resource-optimizer:0-init --enable-cache`

### Run Initial Analysis

- [ ] Execute v7.0 analysis: `/macos-resource-optimizer:1-analyze`
- [ ] Verify execution time: Should complete in 1.5-2.0 seconds
- [ ] Verify output format: Check for `"categories"` key in JSON
- [ ] Verify all 6 categories present:
  - [ ] `cpu` category exists
  - [ ] `memory` category exists
  - [ ] `disk` category exists
  - [ ] `network` category exists
  - [ ] `battery` category exists
  - [ ] `thermal` category exists
- [ ] Save output: `/macos-resource-optimizer:1-analyze > /tmp/v7_analysis_1.json`

### Test Individual Categories

- [ ] Test CPU analysis: `/macos-resource-optimizer:1-analyze --categories cpu`
- [ ] Test memory analysis: `/macos-resource-optimizer:1-analyze --categories memory`
- [ ] Test disk analysis: `/macos-resource-optimizer:1-analyze --categories disk`
- [ ] Test network analysis: `/macos-resource-optimizer:1-analyze --categories network`
- [ ] Test battery analysis: `/macos-resource-optimizer:1-analyze --categories battery`
- [ ] Test thermal analysis: `/macos-resource-optimizer:1-analyze --categories thermal`
- [ ] All commands should complete successfully with JSON output

---

## Phase 6: Update Scripts & Automation (15 minutes)

### Identify Command References

- [ ] Search for v6.0 commands: `grep -r "macos-optimizer:" . --include="*.sh" --include="*.py" --include="*.yml" --include="*.yaml" 2>/dev/null | head -20`
- [ ] Document findings: Save list to `/tmp/command_references.txt`
- [ ] Count references: `grep -r "macos-optimizer:" . --include="*.{sh,py,yml,yaml}" 2>/dev/null | wc -l`

### Update Shell Scripts

- [ ] Find all `.sh` files: `find . -name "*.sh" -type f 2>/dev/null`
- [ ] For each script with v6.0 commands:
  - [ ] Review current content
  - [ ] Update command namespace: `sed -i 's|macos-optimizer:|macos-resource-optimizer:|g' <file>`
  - [ ] Update numeric prefixes if needed
  - [ ] Test updated script: Run with test parameters
  - [ ] Verify output format handling (if parsing response)

### Update Python Scripts

- [ ] Find Python files using old API: `grep -r "macos-optimizer\|cpu_usage_percent\|memory_usage_percent" . --include="*.py" 2>/dev/null`
- [ ] For each Python file:
  - [ ] Review API usage
  - [ ] Update command calls: `old_command` → `/macos-resource-optimizer:X-command`
  - [ ] Update response parsing to handle new nested structure:
    ```python
    # Old: cpu = response['cpu_usage_percent']
    # New: cpu = response['categories']['cpu']['usage_percent']
    ```
  - [ ] Add compatibility function if handling both versions
  - [ ] Test modified script

### Update YAML/JSON Configuration

- [ ] Find config files with optimizer settings: `find . -name "*.yml" -o -name "*.yaml" -o -name "*.json" | xargs grep -l "macos-optimizer" 2>/dev/null`
- [ ] For each config file:
  - [ ] Update command references if present
  - [ ] Update response parsing logic if applicable
  - [ ] Test configuration changes

### Documentation Updates

- [ ] Find documentation files: `find . -name "*.md" | xargs grep -l "macos-optimizer" 2>/dev/null`
- [ ] Update each document:
  - [ ] Replace `/macos-optimizer:` with `/macos-resource-optimizer:`
  - [ ] Update example outputs to show new JSON structure
  - [ ] Update API documentation if present
  - [ ] Add version compatibility notes

### Verify All Updates

- [ ] Final search for old commands: `grep -r "macos-optimizer:" . --include="*.{sh,py,yml,yaml,md}" 2>/dev/null`
- [ ] Should return 0 results (or only in backups/documentation)
- [ ] Spot-check 5 updated files to verify correctness

---

## Phase 7: Run Test Suite (10 minutes)

### Pre-Migration Tests

- [ ] Run v6.0 baseline tests: `pytest .claude/skills/macos-resource-optimizer/.data/tests/ -v --tb=short -k "not migration" 2>&1 | head -50`
- [ ] Check for failures: Should see mostly passes (or manageable failures)

### Migration-Specific Tests

- [ ] Run migration tests: `pytest .claude/skills/macos-resource-optimizer/.data/tests/test_migration.py -v`
- [ ] Expected: All migration tests pass
- [ ] Run compatibility tests: `pytest .claude/skills/macos-resource-optimizer/.data/tests/test_compatibility.py -v`
- [ ] Expected: Compatibility layer working

### Post-Migration Tests

- [ ] Run full test suite: `pytest .claude/skills/macos-resource-optimizer/.data/tests/ -v`
- [ ] Count passed tests: `pytest .claude/skills/macos-resource-optimizer/.data/tests/ -v 2>&1 | grep -E "passed|failed" | tail -1`
- [ ] Verify coverage: `pytest .claude/skills/macos-resource-optimizer/.data/tests/ --cov=.claude/skills/macos-resource-optimizer/.data --cov-report=term-missing 2>&1 | tail -10`
- [ ] Coverage should be ≥86%
- [ ] All tests should pass

### Specific Test Categories

- [ ] Test API compatibility: `pytest .claude/skills/macos-resource-optimizer/.data/tests/test_api_compatibility.py -v`
- [ ] Test configuration: `pytest .claude/skills/macos-resource-optimizer/.data/tests/test_config.py -v`
- [ ] Test commands: `pytest .claude/skills/macos-resource-optimizer/.data/tests/test_commands.py -v`
- [ ] Test performance: `pytest .claude/skills/macos-resource-optimizer/.data/tests/test_performance.py -v`
- [ ] All test categories should pass

---

## Phase 8: Performance Verification (5 minutes)

### Benchmark Execution Time

- [ ] Run analysis once (cold cache): `/macos-resource-optimizer:1-analyze` and note time
- [ ] Expected: 1.5-2.0 seconds
- [ ] Run analysis again (warm cache): `/macos-resource-optimizer:1-analyze --cache` and note time
- [ ] Expected: ~0.5 seconds (if cache hit)

### Run Performance Benchmark

- [ ] Create benchmark script:
  ```bash
  #!/bin/bash
  echo "Performance Benchmark"
  for i in {1..5}; do
    echo "Run $i (with cache):"
    /usr/bin/time -p /macos-resource-optimizer:1-analyze --cache 2>&1 | grep real
    sleep 1
  done
  ```
- [ ] Execute benchmark: `bash benchmark.sh`
- [ ] Average execution time should be 1.5-2.0s
- [ ] Verify 40% improvement vs v6.0's 2.5s

### Compare with v6.0 Baseline

- [ ] Run parallel benchmark (if v6.0 still accessible): Compare execution times
- [ ] v7.0 should be consistently 40% faster
- [ ] Document results for your records

---

## Phase 9: Data Validation (10 minutes)

### Verify Output Accuracy

- [ ] Run analysis: `/macos-resource-optimizer:1-analyze > /tmp/v7_analysis.json`
- [ ] Check JSON validity: `python -m json.tool /tmp/v7_analysis.json > /dev/null && echo "✅ Valid JSON"`
- [ ] Verify structure: `python -c "import json; d=json.load(open('/tmp/v7_analysis.json')); assert 'categories' in d; print('✅ Structure OK')"`
- [ ] Verify all 6 categories:
  ```bash
  python -c "
  import json
  d = json.load(open('/tmp/v7_analysis.json'))
  cats = d['categories']
  for cat in ['cpu', 'memory', 'disk', 'network', 'battery', 'thermal']:
    assert cat in cats, f'Missing {cat}'
  print('✅ All categories present')
  "
  ```

### Compare with v6.0 Data

- [ ] Extract CPU metrics from both:
  ```bash
  CPU_V6=$(python -c "import json; print(json.load(open('/tmp/v6_baseline.json'))['cpu_usage_percent'])" 2>/dev/null)
  CPU_V7=$(python -c "import json; print(json.load(open('/tmp/v7_analysis.json'))['categories']['cpu']['usage_percent'])" 2>/dev/null)
  echo "v6.0 CPU: $CPU_V6%, v7.0 CPU: $CPU_V7%"
  ```
- [ ] Verify difference is ≤5% (allows for system variance)
- [ ] Repeat for other metrics (memory, disk usage)
- [ ] Values should be similar (±5% acceptable)

### Validate Metrics Ranges

- [ ] CPU usage: Should be 0-100%
- [ ] Memory usage: Should be 0-100%
- [ ] Disk usage: Should be 0-100%
- [ ] Battery: Should be 0-100% (or "plugged in")
- [ ] Temperature: Should be 30-80°C (typical range)
- [ ] All values within expected ranges

---

## Phase 10: Comprehensive Validation (10 minutes)

### Full Feature Test

- [ ] Test init: `/macos-resource-optimizer:0-init --full-validation`
- [ ] Test analyze: `/macos-resource-optimizer:1-analyze` (multiple runs)
- [ ] Test optimize: `/macos-resource-optimizer:2-optimize --dry-run`
- [ ] Test monitor: `/macos-resource-optimizer:3-monitor --duration 5s`
- [ ] Test report: `/macos-resource-optimizer:4-report --type summary`
- [ ] All commands should complete successfully

### Error Handling

- [ ] Test invalid category: `/macos-resource-optimizer:1-analyze --categories invalid` (should error gracefully)
- [ ] Test help output: `/macos-resource-optimizer:1-analyze --help` (should show help)
- [ ] Test with no args: `/macos-resource-optimizer:1-analyze` (should work with defaults)

### Integration Test

- [ ] Run complete workflow:
  ```bash
  /macos-resource-optimizer:0-init
  /macos-resource-optimizer:1-analyze
  /macos-resource-optimizer:2-optimize --dry-run
  /macos-resource-optimizer:3-monitor --duration 3s
  /macos-resource-optimizer:4-report --type summary
  ```
- [ ] All steps should complete without errors

---

## Phase 11: Documentation & Training (5 minutes)

### Update Team Documentation

- [ ] Create migration summary for team
- [ ] Document command mapping: Old → New
- [ ] Share updated API reference
- [ ] Provide example updated scripts
- [ ] Note any special considerations for your environment

### Create Runbooks

- [ ] Command quick reference sheet
- [ ] Troubleshooting guide for team
- [ ] Escalation procedures
- [ ] Emergency rollback procedure

### Knowledge Transfer

- [ ] Brief team on changes
- [ ] Demo new commands
- [ ] Review new features (caching, parallelization)
- [ ] Answer questions

---

## Phase 12: Post-Migration Cleanup (5 minutes)

### Archive Old Configuration

- [ ] Archive v6.0 config: `gzip -k .claude/skills/macos-resource-optimizer/.data/config.yaml.v6.baseline`
- [ ] Store securely: Move to backup location if desired
- [ ] Document storage location

### Cleanup Temporary Files

- [ ] Remove temp analysis files: `rm -f /tmp/v6_baseline*.json /tmp/v7_analysis*.json`
- [ ] Clean up conversion temp files: `rm -f .claude/skills/macos-resource-optimizer/.data/config.yaml.temp`
- [ ] Cleanup scripts: `rm -f benchmark.sh`

### Document Migration Completion

- [ ] Record completion date and time
- [ ] Note any issues encountered and resolution
- [ ] Document execution times achieved
- [ ] Note any team feedback
- [ ] Create completion report

### Commit Changes (if using git)

- [ ] Stage modified files: `git add .claude/skills/macos-resource-optimizer/.data/ .claude/`
- [ ] Commit with message: `git commit -m "Migrate macOS Resource Optimizer v6.0 → v7.0"`
- [ ] Push to repository: `git push` (if applicable)

---

## Phase 13: Post-Migration Monitoring (Ongoing)

### Daily Checks (First 7 Days)

- [ ] Day 1: Run full workflow once
- [ ] Day 2: Verify caching works (run twice, check speed difference)
- [ ] Day 3: Test optimization mode
- [ ] Day 4: Test monitoring mode
- [ ] Day 5: Run full test suite
- [ ] Day 6: Check logs for any errors
- [ ] Day 7: Generate weekly report

### Weekly Monitoring (Next 3 Weeks)

- [ ] Week 1: Verify all commands working
- [ ] Week 2: Benchmark performance consistency
- [ ] Week 3: Check for any edge cases
- [ ] Week 4: Confirm stable operation

### Monthly Review

- [ ] Run health check: `/macos-resource-optimizer:0-init --health-check`
- [ ] Generate performance report
- [ ] Review any issues or errors from logs
- [ ] Verify test coverage remains ≥86%

---

## Phase 14: Backup Retention

### Backup Management Strategy

**Short-term** (Keep for 7 days):
- [ ] `.claude/skills/macos-resource-optimizer/.data.v6.backup/` directory (in project)
- [ ] Daily snapshots in `/tmp/` (if automated backups enabled)

**Medium-term** (Keep for 30 days):
- [ ] `macos-optimizer-v6-backup-*.tar.gz` in `~/.backups/`
- [ ] Useful for emergency rollback

**Long-term** (Keep for 90 days):
- [ ] Archive to storage system (optional)
- [ ] One snapshot per week

### Backup Cleanup Schedule

- [ ] After 7 days: Remove `.claude/skills/macos-resource-optimizer/.data.v6.backup/` directory if migration stable
- [ ] After 30 days: Move archives to long-term storage
- [ ] After 90 days: Delete archives

### Verify Backup Still Works (Every 30 days)

- [ ] Test extraction: `tar -tzf macos-optimizer-v6-backup-*.tar.gz > /dev/null`
- [ ] Spot check contents: `tar -tzf macos-optimizer-v6-backup-*.tar.gz | head -10`
- [ ] Keep test successful: Confirm backup remains valid

---

## Rollback Checklist (If Needed)

If you need to rollback to v6.0 at any point:

### Quick Rollback

- [ ] Stop all v7.0 processes: `pkill -f macos-resource-optimizer`
- [ ] Remove v7.0: `rm -rf .claude/commands/macos-resource-optimizer/`
- [ ] Restore v6.0: `rm -rf .claude/skills/macos-resource-optimizer/.data && mv .claude/skills/macos-resource-optimizer/.data.v6.backup .claude/skills/macos-resource-optimizer/.data`
- [ ] Verify v6.0: `/macos-optimizer:analyze --version`
- [ ] Run tests: `pytest .claude/skills/macos-resource-optimizer/.data/tests/ -v`

### Full Rollback (Using Archive)

- [ ] Stop processes: `pkill -f "macos-resource"`
- [ ] Extract backup: `tar -xzf macos-optimizer-v6-backup-*.tar.gz`
- [ ] Restore: `rm -rf .claude/skills/macos-resource-optimizer/.data && mv .claude/skills/macos-resource-optimizer/.data.v6.backup .claude/skills/macos-resource-optimizer/.data`
- [ ] Verify: `/macos-optimizer:analyze --version`
- [ ] Test: `pytest .claude/skills/macos-resource-optimizer/.data/tests/ -v`

---

## Success Indicators

You have successfully migrated when:

### All Green Lights (Required)

- [ ] ✅ Init command completes: `/macos-resource-optimizer:0-init`
- [ ] ✅ Analysis executes in 1.5-2.0s: `/macos-resource-optimizer:1-analyze`
- [ ] ✅ All tests pass: `pytest .claude/skills/macos-resource-optimizer/.data/tests/`
- [ ] ✅ Test coverage ≥86%
- [ ] ✅ JSON response valid with `categories` structure
- [ ] ✅ All 6 resource categories analyzed correctly
- [ ] ✅ No errors in logs

### Performance Confirmed

- [ ] ✅ Execution time: 1.5-2.0s (vs 2.5s in v6.0)
- [ ] ✅ Cache hit speedup: ~0.5s when cache enabled
- [ ] ✅ Parallel execution working (all 6 categories in parallel)

### Data Validated

- [ ] ✅ CPU, Memory, Disk, Network, Battery, Thermal metrics valid
- [ ] ✅ Metrics within expected ranges
- [ ] ✅ Comparison with v6.0 within ±5%

### Operations Ready

- [ ] ✅ All scripts updated to v7.0 commands
- [ ] ✅ API parsers handle new response format
- [ ] ✅ Configuration migrated and validated
- [ ] ✅ Backup created and tested
- [ ] ✅ Team trained on changes

---

## Support & Issues

### If You Encounter Problems

- [ ] Refer to "Troubleshooting Guide" in [MIGRATION_v6_to_v7.md](MIGRATION_v6_to_v7.md)
- [ ] Check logs: `tail -f .claude/skills/macos-resource-optimizer/.data/logs/migration.log`
- [ ] Report feedback: `/macos-resource-optimizer:9-feedback --type issue`

### Emergency Contacts

- Documentation: [MIGRATION_v6_to_v7.md](MIGRATION_v6_to_v7.md)
- Issue Tracker: GitHub Issues
- Support: `/macos-resource-optimizer:9-feedback`

---

## Summary

**Phases Completed**: ___/14

**Time Spent**: _____ minutes (Expected: 45-60)

**Migration Date**: ______________

**Completed By**: ______________

**Issues Encountered**:
```
[Document any issues and resolutions]
```

**Notes**:
```
[Add any additional notes or observations]
```

---

**Migration Status**: □ In Progress | □ Complete | □ Rolled Back

**Sign-off**: _________________________ Date: _____________

---

**Version**: 1.0.0
**Last Updated**: 2025-11-30
**Status**: Ready for Use

For detailed information, see [MIGRATION_v6_to_v7.md](MIGRATION_v6_to_v7.md)
