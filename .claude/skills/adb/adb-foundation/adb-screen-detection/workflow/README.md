# adb-screen-detection Workflows

Workflow infrastructure for Screen content detection and OCR analysis

## Overview

This directory contains TOON-based workflow definitions for automating Screen content detection and OCR analysis workflows. Each workflow pairs a `.toon` file (orchestration logic) with a `.md` file (documentation).

## Workflow Index

### Implemented Workflows (2 TOON+MD pairs)

1. **[template-matching.md](./template-matching.md)** - Template image matching
   - File: `template-matching.toon`
   - Match templates against screen
   - Configurable confidence thresholds
   - Locate UI elements by pattern

2. **[ocr-detection.md](./ocr-detection.md)** - OCR text-based detection
   - File: `ocr-detection.toon`
   - Extract text from screen
   - Search for specific text
   - Multi-language support (Korean/English)

## Purpose

TOON (Task-Oriented Orchestration Notation) workflows provide:
- Structured task orchestration and sequencing
- Parameter validation and passing
- Multi-phase execution workflows
- Integration with adb-workflow-orchestrator
- Comprehensive error handling and recovery

## Usage

Execute any workflow using the ADB workflow orchestrator:

```bash
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-screen-detection/workflow/{workflow-name}.toon \
  --param device="127.0.0.1:5555" \
  --verbose
```

## Workflow Structure

Each workflow consists of two files:

### TOON File (Orchestration)
The `.toon` file defines:
- Workflow parameters and validation
- Execution phases and sequential steps
- Error handling and recovery actions
- Output and reporting

### Markdown File (Documentation)
The `.md` file documents:
- Purpose and use case
- Prerequisites and requirements
- Available parameters and constraints
- Execution phases and expected outputs
- Success criteria and error handling
- Example commands and integration patterns

## Creating New Workflows

To create a new workflow:

1. Create `{name}.toon` file using TOON v4.0 syntax
2. Create `{name}.md` documentation file
3. Test execution with workflow orchestrator
4. Update this README.md index

Refer to [pattern-toon-workflow.md](./../../builder/modules/pattern-toon-workflow.md) for detailed TOON patterns and specifications.

## Integration

These workflows integrate with:
- `adb-workflow-orchestrator` - Execution engine
- Other ADB skills for automation chains

## References

- TOON v4.0 Specification: [pattern-toon-workflow.md](./../../builder/modules/pattern-toon-workflow.md)
- Workflow Orchestrator: [adb-workflow-orchestrator SKILL.md](../adb-workflow-orchestrator/SKILL.md)
- Parent Skill: [SKILL.md](../SKILL.md)

---

**Status**: Phase 6B - Complete (2 TOON+MD workflow pairs created)
**Last Updated**: 2025-12-02
