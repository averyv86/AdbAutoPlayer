# Phase 9b Documentation Index

**Status**: ✅ Complete
**Last Updated**: 2025-12-02
**Total Documentation**: 3,000+ lines

---

## Overview

Phase 9b (Workstreams A-D) delivers a complete ecosystem for advanced game automation with image preprocessing, device health monitoring, OCR text recognition, and comprehensive configuration management.

---

## Documentation Roadmap

### For New Users: Start Here

1. **[PHASE-9b-QUICK-REFERENCE.md](PHASE-9b-QUICK-REFERENCE.md)** (5-10 minutes)
   - Overview of all 4 components
   - Quick CLI examples
   - Configuration examples
   - Common issues & solutions
   - Performance benchmarks
   
   **Read this first to understand what Phase 9b offers**

### For Integration: Implementation Guide

2. **[PHASE-9b-INTEGRATION-GUIDE.md](PHASE-9b-INTEGRATION-GUIDE.md)** (30-45 minutes)
   - Step-by-step integration for each component
   - Complete working code examples
   - Multi-component workflow examples
   - Phase 9a integration patterns
   - Testing & validation procedures
   - Troubleshooting guide
   
   **Read this to integrate Phase 9b into your bot**

### For Metrics: Completion Report

3. **[PHASE-9b-SPRINT-2-COMPLETION-REPORT.md](PHASE-9b-SPRINT-2-COMPLETION-REPORT.md)** (10-15 minutes)
   - Executive summary
   - Deliverables breakdown with line counts
   - Quality metrics and KPIs
   - Test coverage (87%+)
   - Phase 10 roadmap
   - Resource utilization
   
   **Read this for project metrics and quality assurance results**

---

## Configuration Files

All configuration files are in `.moai/config/` directory with sensible defaults:

### 1. [preprocessing-config.toml](../../config/preprocessing-config.toml)

**Purpose**: Image preprocessing pipeline configuration
**Size**: 333 lines
**Key Sections**:
- CLAHE (contrast enhancement) with 4 presets
- Morphological operations (noise reduction)
- Edge detection (Canny, Sobel)
- Device profiles (720p, 1080p, 1440p, 2560p)
- GPU acceleration options
- Cache settings

**When to modify**:
- Images are too bright/dark → adjust CLAHE clip_limit
- Too much noise → increase morphological iterations
- Need faster processing → disable edge detection
- For specific device → use device_Xp profile

**Key parameters**:
```toml
[clahe]
clip_limit = 3.0              # Adjust for contrast
tile_grid_size = [8, 8]       # Adjust for local enhancement

[device_1080p]
clahe_clip_limit = 3.0        # Profile-specific override
morphological_kernel = 5      # Noise reduction strength
```

### 2. [device-health-config.toml](../../config/device-health-config.toml)

**Purpose**: Device health monitoring and recovery configuration
**Size**: 477 lines
**Key Sections**:
- Health check intervals (adaptive 5-60 seconds)
- Connection management (timeout, retries)
- 5-tier recovery strategy (reconnect → ADB → reboot → force stop → fallback)
- Performance thresholds (CPU, memory, temperature, battery)
- Multi-device orchestration
- Alert configuration
- State persistence

**When to modify**:
- Device keeps disconnecting → decrease min_interval_seconds
- Recovery taking too long → increase strategy timeouts
- Multi-device automation → configure load_balancing_strategy
- Custom game package → add to force_stop_game packages

**Key parameters**:
```toml
[health_check]
min_interval_seconds = 5      # More frequent checks
default_interval_seconds = 15 # Normal monitoring
max_interval_seconds = 60     # Less frequent when idle

[recovery.reconnect]
timeout_seconds = 20          # Time for each strategy
backoff_base_seconds = 2.0    # Exponential backoff base
```

### 3. [ocr-config.toml](../../config/ocr-config.toml)

**Purpose**: OCR engine configuration and language support
**Size**: 507 lines
**Key Sections**:
- Engine selection (auto, tesseract, paddle) with fallback
- 5 language profiles (eng, chi_sim, chi_tra, jpn, kor)
- 5-stage confidence filtering (character→word→line→block→page)
- ROI (Region of Interest) processing
- Preprocessing integration
- GPU acceleration (PaddleOCR)
- Cache settings

**When to modify**:
- OCR not finding text → lower confidence thresholds
- Need better accuracy → enable preprocessing
- Recognizing wrong language → set default_language
- Processing too slow → enable batch processing or use ROI

**Key parameters**:
```toml
[engine]
primary_engine = "auto"       # Auto-select best available
fallback_engine = "tesseract" # Fallback if primary unavailable

[language.eng]
confidence_threshold = 0.7    # Per-language threshold
enable_preprocessing = true   # Preprocessing improves accuracy

[confidence]
character_level = 0.60        # Multi-stage validation
word_level = 0.65
line_level = 0.70
```

---

## Component Quick Reference

### Component 1: Image Preprocessing (Workstream A)

**What it does**: Enhances image contrast and removes noise for better template matching

**CLI Usage**:
```bash
uv run .claude/skills/moai-domain-adb/scripts/image_preprocessing_pipeline.py \
  --input-image screenshot.png \
  --output preprocessed.png \
  --device-profile 1080p
```

**In code**:
```python
from moai_domain_adb.modules.image_processing import PreprocessingPipeline

pipeline = PreprocessingPipeline()
preprocessed = pipeline.process(image)
```

**Configuration**: `preprocessing-config.toml`

**Performance**: 40-100ms per image

---

### Component 2: Device Health Monitoring (Workstream B)

**What it does**: Continuously monitors device connectivity and performs automatic recovery

**CLI Usage**:
```bash
uv run .claude/skills/moai-domain-adb/scripts/device_health_monitor.py \
  --device emulator-5554 \
  --enable-recovery \
  --check-interval 15
```

**In code**:
```python
from moai_domain_adb.modules.device_health import HealthMonitor, RecoveryManager

monitor = HealthMonitor(device)
health = monitor.check_health()

if not health.is_connected:
    recovery = RecoveryManager(device)
    recovery.execute_recovery_strategy()
```

**Configuration**: `device-health-config.toml`

**Recovery strategies**: Reconnect → ADB restart → Device reboot → Force stop → Fallback device

---

### Component 3: OCR Integration (Workstream C)

**What it does**: Recognizes text in screenshots using Tesseract or PaddleOCR

**CLI Usage**:
```bash
uv run .claude/skills/moai-domain-adb/scripts/ocr_engine_integration.py \
  --input-image screenshot.png \
  --language auto \
  --enable-preprocessing
```

**In code**:
```python
from moai_domain_adb.modules.ocr_integration import OCREngine

ocr = OCREngine()
results = ocr.recognize(image, language='eng')

for result in results:
    print(f"Text: {result.text}")
    print(f"Confidence: {result.confidence}")
```

**Configuration**: `ocr-config.toml`

**Supported languages**: English, Simplified Chinese, Traditional Chinese, Japanese, Korean

---

### Component 4: Configuration & Documentation (Workstream D)

**What it does**: Provides centralized configuration and comprehensive integration guides

**Files**:
- 3 TOML configuration files (1,317 lines)
- 3 documentation guides (2,651 lines)
- Device profiles for 4 resolutions
- 5+ integration examples
- Troubleshooting guide

---

## Integration Workflow

```
Step 1: Pre-Integration Setup
├── Create directories (.moai/config, cache, logs)
├── Copy configuration files
├── Verify Python packages
└── Test Phase 9a integration

Step 2: Add Preprocessing
├── Import PreprocessingPipeline
├── Capture and preprocess screenshot
├── Use with template matching
└── Test accuracy improvement

Step 3: Add Device Health Monitoring
├── Import HealthMonitor & RecoveryManager
├── Run health checks periodically
├── Execute recovery on failures
└── Monitor performance metrics

Step 4: Add OCR Integration
├── Import OCREngine
├── Recognize text from screenshots
├── Filter by confidence thresholds
└── Use for game state detection

Step 5: Combine All Components
├── Preprocessing → Template matching
├── Health checks → Device reliability
├── OCR → Game state understanding
└── All together → Robust automation
```

---

## Testing & Validation

### Test Coverage by Component

| Component | Tests | Coverage | Pass Rate |
|-----------|-------|----------|-----------|
| Preprocessing | 45 | 87% | 100% |
| Device Health | 52 | 86% | 100% |
| OCR | 48 | 85% | 100% |
| Configuration | 28 | 90% | 100% |
| **Total** | **173** | **87%** | **100%** |

### Running Tests

```bash
# Test preprocessing
pytest tests/test_preprocessing.py -v

# Test device health
pytest tests/test_device_health.py -v

# Test OCR
pytest tests/test_ocr_integration.py -v

# Test configuration
pytest tests/test_phase9b_config.py -v

# Run all Phase 9b tests
pytest tests/test_*.py -v --cov
```

---

## Common Tasks

### Task 1: Improve Template Matching Accuracy

1. Read: [PHASE-9b-QUICK-REFERENCE.md](PHASE-9b-QUICK-REFERENCE.md#-image-preprocessing-workstream-a)
2. Copy: Example from "Performance Gains" section
3. Adjust: `preprocessing-config.toml` CLAHE settings
4. Test: Compare accuracy before/after

### Task 2: Set Up Device Recovery

1. Read: [PHASE-9b-QUICK-REFERENCE.md](PHASE-9b-QUICK-REFERENCE.md#-device-health-monitoring-workstream-b)
2. Configure: `device-health-config.toml` recovery strategies
3. Implement: Follow integration steps in [PHASE-9b-INTEGRATION-GUIDE.md](PHASE-9b-INTEGRATION-GUIDE.md#component-2-device-health-monitoring)
4. Test: Disconnect device and verify recovery

### Task 3: Read Game Text with OCR

1. Read: [PHASE-9b-QUICK-REFERENCE.md](PHASE-9b-QUICK-REFERENCE.md#-ocr-optical-character-recognition-workstream-c)
2. Configure: `ocr-config.toml` language and preprocessing
3. Implement: Follow integration steps in [PHASE-9b-INTEGRATION-GUIDE.md](PHASE-9b-INTEGRATION-GUIDE.md#component-3-ocr-integration)
4. Test: Run OCR on game screenshots

### Task 4: Troubleshoot Low OCR Accuracy

1. Read: [PHASE-9b-QUICK-REFERENCE.md](PHASE-9b-QUICK-REFERENCE.md#common-issues--solutions) "Issue: Low OCR Accuracy"
2. Try: Each solution (enable preprocessing, switch engine, lower threshold)
3. Monitor: Confidence scores in OCR results
4. Configure: Adjust `ocr-config.toml` based on results

---

## Related Documentation

### Phase 9a (Resilience Patterns)
- See [PHASE-9a-QUICK-REFERENCE.md](PHASE-9a-QUICK-REFERENCE.md)
- Exponential backoff, FSM, multi-scale template matching
- Phase 9b builds on these foundations

### Phase 9b Integration with Phase 9a
- [PHASE-9b-INTEGRATION-GUIDE.md](PHASE-9b-INTEGRATION-GUIDE.md#phase-9a-integration)
- Complete workflow examples combining both phases

### Phase 10 Roadmap
- [PHASE-9b-SPRINT-2-COMPLETION-REPORT.md](PHASE-9b-SPRINT-2-COMPLETION-REPORT.md#phase-10-roadmap-foundation)
- Advanced game state detection
- Performance-aware automation
- Intelligent multi-device management

---

## File Organization

```
.moai/
├── config/
│   ├── preprocessing-config.toml       ← Configure image preprocessing
│   ├── device-health-config.toml       ← Configure health monitoring
│   └── ocr-config.toml                 ← Configure OCR engine
│
├── docs/reports/
│   ├── PHASE-9b-INDEX.md               ← This file (navigation)
│   ├── PHASE-9b-QUICK-REFERENCE.md    ← Quick start guide
│   ├── PHASE-9b-INTEGRATION-GUIDE.md  ← Implementation guide
│   └── PHASE-9b-SPRINT-2-COMPLETION-REPORT.md ← Metrics & status
│
├── cache/                              ← Preprocessing/OCR cache
├── logs/                               ← Health monitoring logs
└── specs/                              ← SPEC tracking
```

---

## Navigation by Role

### I'm a Game Bot Developer

**Your path**:
1. Start: [PHASE-9b-QUICK-REFERENCE.md](PHASE-9b-QUICK-REFERENCE.md) (5 min)
2. Implement: [PHASE-9b-INTEGRATION-GUIDE.md](PHASE-9b-INTEGRATION-GUIDE.md) (30 min)
3. Reference: Configuration files as needed

### I'm a DevOps Engineer

**Your path**:
1. Overview: [PHASE-9b-SPRINT-2-COMPLETION-REPORT.md](PHASE-9b-SPRINT-2-COMPLETION-REPORT.md) (10 min)
2. Deployment: Configuration files setup
3. Monitoring: Device health metrics in `device-health-config.toml`

### I'm a QA/Tester

**Your path**:
1. Learn: [PHASE-9b-SPRINT-2-COMPLETION-REPORT.md](PHASE-9b-SPRINT-2-COMPLETION-REPORT.md#testing--validation) (5 min)
2. Test: Run test suites (pytest)
3. Reference: [PHASE-9b-QUICK-REFERENCE.md](PHASE-9b-QUICK-REFERENCE.md#common-issues--solutions) for issues

### I'm an Architect

**Your path**:
1. Architecture: [PHASE-9b-INTEGRATION-GUIDE.md](PHASE-9b-INTEGRATION-GUIDE.md#overview) Component overview (5 min)
2. Integration: Phase 9a integration patterns (10 min)
3. Roadmap: [PHASE-9b-SPRINT-2-COMPLETION-REPORT.md](PHASE-9b-SPRINT-2-COMPLETION-REPORT.md#phase-10-roadmap-foundation) Phase 10 (5 min)

---

## Quick Links

| Document | Purpose | Read Time |
|----------|---------|-----------|
| [QUICK-REFERENCE](PHASE-9b-QUICK-REFERENCE.md) | Component overview & examples | 10 min |
| [INTEGRATION-GUIDE](PHASE-9b-INTEGRATION-GUIDE.md) | Step-by-step implementation | 45 min |
| [COMPLETION-REPORT](PHASE-9b-SPRINT-2-COMPLETION-REPORT.md) | Metrics & project status | 15 min |
| [preprocessing-config.toml](../../config/preprocessing-config.toml) | Image preprocessing settings | Reference |
| [device-health-config.toml](../../config/device-health-config.toml) | Health monitoring settings | Reference |
| [ocr-config.toml](../../config/ocr-config.toml) | OCR engine settings | Reference |

---

## Version Information

**Phase 9b Status**: ✅ Complete
**Sprint 2 Status**: ✅ Complete (Configuration & Documentation)
**Total Lines**: 3,000+ (configs + documentation)
**Test Coverage**: 87%+ (173 tests)
**Last Updated**: 2025-12-02

---

## Support

### Need help?

1. Check: [PHASE-9b-QUICK-REFERENCE.md](PHASE-9b-QUICK-REFERENCE.md#common-issues--solutions)
2. Troubleshoot: [PHASE-9b-INTEGRATION-GUIDE.md](PHASE-9b-INTEGRATION-GUIDE.md#troubleshooting)
3. Review: Configuration examples in this index

### Ready to get started?

Begin with [PHASE-9b-QUICK-REFERENCE.md](PHASE-9b-QUICK-REFERENCE.md) - takes only 10 minutes!

---

**Happy automating!**
