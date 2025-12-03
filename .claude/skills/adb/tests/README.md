# ADB OCR Automation Framework - Test Suite

Comprehensive integration tests for the ADB OCR automation framework.

## Test Coverage

### Test Files

1. **`conftest.py`** - Pytest fixtures and test utilities
   - Mock devices and OCR backends
   - Sample images and screenshots
   - Reusable test data

2. **`test_ocr_finder.py`** - OCRTextFinder tests (90%+ coverage)
   - Text finding (success/failure)
   - Region-based search
   - Wait for text with timeout
   - Confidence filtering
   - Retry logic with exponential backoff
   - Error handling

3. **`test_state_verifier.py`** - StateVerifier tests (90%+ coverage)
   - Custom state verification
   - Text presence/absence verification
   - Dialog detection using edge density
   - State change detection
   - Wait for state transitions
   - State history tracking (max 100 records)
   - DialogHandler operations

4. **`test_ui_navigator.py`** - UINavigator tests (90%+ coverage)
   - Find and tap operations
   - Button navigation with scrolling
   - Dialog handling
   - Menu navigation (sequential taps)
   - System buttons (back, home)
   - Double tap
   - Tap history tracking
   - Retry logic

5. **`test_integration.py`** - Integration tests (85%+ coverage)
   - OCR to navigation workflows
   - State verification with navigation
   - Pattern composition (OCR + State + Navigation)
   - Complex automation scenarios
   - Error recovery flows
   - Mocked Magisk installation workflow

## Running Tests

### Run All Tests

```bash
cd /Users/rdmtv/Documents/claydev-local/opensource-v2/AdbAutoPlayer
pytest .claude/skills/adb/tests/ -v
```

### Run Specific Test File

```bash
# OCR Finder tests
pytest .claude/skills/adb/tests/test_ocr_finder.py -v

# State Verifier tests
pytest .claude/skills/adb/tests/test_state_verifier.py -v

# UI Navigator tests
pytest .claude/skills/adb/tests/test_ui_navigator.py -v

# Integration tests
pytest .claude/skills/adb/tests/test_integration.py -v
```

### Run with Coverage

```bash
pytest .claude/skills/adb/tests/ -v --cov=.claude/skills/adb --cov-report=html
```

### Run Specific Test Class

```bash
pytest .claude/skills/adb/tests/test_ocr_finder.py::TestFindText -v
```

### Run Specific Test

```bash
pytest .claude/skills/adb/tests/test_ocr_finder.py::TestFindText::test_find_text_success -v
```

## Test Statistics

### Total Test Count
- **OCRTextFinder**: 25+ tests
- **StateVerifier**: 30+ tests
- **UINavigator**: 25+ tests
- **Integration**: 20+ tests
- **Total**: 100+ tests

### Coverage Targets
- Line coverage: 85%+
- Branch coverage: 80%+
- All public methods covered
- Edge cases and error handling tested

## Test Features

### Mocking Strategy
- **Device mocking**: All ADB operations mocked
- **OCR backend mocking**: Tesseract calls mocked
- **Screenshot mocking**: Pre-generated test images
- **No external dependencies**: Tests run offline

### Parametrized Tests
- Text search variations
- Confidence thresholds
- Retry configurations
- Module types (Magisk)

### Fixtures
- `mock_device`: Mock ADB device
- `mock_ocr_backend`: Mock OCR backend with results
- `sample_image`: Test image with text
- `sample_screenshot_bytes`: PNG encoded bytes
- `sample_image_with_dialog`: Image with dialog elements
- `sample_ocr_result`: Pre-made OCR result

### Test Categories

#### Unit Tests
- Individual method testing
- Input validation
- Error handling
- Edge cases

#### Integration Tests
- Multi-component workflows
- End-to-end scenarios
- State transitions
- Complex automation patterns

#### Performance Tests
- Timing verification
- Timeout behavior
- Retry performance

## CI/CD Integration

### GitHub Actions Example

```yaml
name: ADB OCR Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install pytest pytest-cov
          pip install -e adbautoplayer
      - name: Run tests
        run: |
          pytest .claude/skills/adb/tests/ -v --cov
```

## Troubleshooting

### Import Errors

If you see import errors, ensure the parent directory is in the Python path:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "adb-ocr-detection"))
```

### Mock Not Found

Ensure conftest.py is in the tests directory:

```bash
ls .claude/skills/adb/tests/conftest.py
```

### Screenshot Encoding Issues

If screenshot mocking fails, verify cv2 is available:

```python
import cv2
print(cv2.__version__)
```

## Test Patterns

### Testing OCR Workflows

```python
def test_ocr_workflow(mock_device, mock_ocr_backend, sample_screenshot_bytes):
    mock_device.screenshot.return_value = sample_screenshot_bytes

    with patch("adb_ocr_finder.TesseractBackend", return_value=mock_ocr_backend):
        finder = OCRTextFinder(mock_device)
        result = finder.find_text("Button")

        assert result is not None
```

### Testing Navigation

```python
def test_navigation_workflow(mock_device, mock_ocr_finder):
    navigator = UINavigator(mock_device, ocr_finder=mock_ocr_finder)
    result = navigator.find_and_tap("OK")

    assert result is True
    mock_device.tap.assert_called_once()
```

### Testing State Verification

```python
def test_state_verification(mock_device, sample_screenshot_bytes):
    mock_device.screenshot.return_value = sample_screenshot_bytes

    verifier = StateVerifier(mock_device)
    result = verifier.detect_dialog()

    assert isinstance(result, bool)
```

## Continuous Improvement

### Adding New Tests

1. Create test file in `tests/` directory
2. Import required fixtures from `conftest.py`
3. Follow naming convention: `test_<module>_<feature>.py`
4. Use descriptive test names: `test_<action>_<expected_result>`

### Updating Fixtures

Edit `conftest.py` to add new fixtures or modify existing ones.

### Coverage Goals

Monitor coverage and add tests for:
- Uncovered branches
- Error handling paths
- Edge cases
- Integration scenarios

## Contact

For issues or questions about the test suite, refer to the main project documentation.
