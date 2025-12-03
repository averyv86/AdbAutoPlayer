# Testing Checklist - MoAI Tab Suspender

> **Quick validation checklist for Phase 1 (MVP) testing**
> **Version**: 1.0.0
> **Last Updated**: 2025-12-01

---

## Pre-Installation Checklist

- [ ] Python 3.11+ installed
- [ ] UV installed (`uv --version` works)
- [ ] Chrome or Dia Browser installed
- [ ] Developer mode can be enabled in browser

---

## Installation Testing

### Step 1: Run Installer

```bash
cd extensions/chrome-tab-suspender
./install.sh
```

- [ ] Script starts successfully
- [ ] Extension files verified (manifest.json, background.js)
- [ ] Host script verified (tab_suspender.py)
- [ ] Prompted for manual extension installation
- [ ] Extension ID prompt appears
- [ ] Native Messaging manifest created at `~/.moai/bin/com.moai.tab_suspender.json`
- [ ] Chrome NativeMessagingHosts symlink created
- [ ] (Optional) Dia Browser NativeMessagingHosts symlink created
- [ ] Test connection runs at end

### Step 2: Verify Extension Installation

Open: `chrome://extensions/`

- [ ] Extension appears in list
- [ ] Extension name: "MoAI Tab Suspender"
- [ ] Version: "1.0.0"
- [ ] Status: Enabled (toggle is ON)
- [ ] No error messages shown
- [ ] Extension ID is 32 lowercase letters

### Step 3: Verify Native Messaging

```bash
uv run scripts/tab_suspender.py --test
```

**Expected output**:
- [ ] ✅ Found Native Messaging manifest
- [ ] ✅ Manifest valid: com.moai.tab_suspender
- [ ] ✅ Host script exists
- [ ] ✅ Extension connection successful

**If any ❌ appear**: See Troubleshooting section in README.md

---

## Functional Testing

### Test 1: Manual Tab Suspension

**Setup**:
1. Open Chrome
2. Open 10-20 tabs (mix of different sites)
3. Pin 2-3 tabs
4. Keep one tab active

**Execute**:
```bash
uv run scripts/tab_suspender.py --suspend --browser=chrome
```

**Verify**:
- [ ] Command completes within 5 seconds
- [ ] Output shows TOON format: `browser:Chrome|tabs:X|suspended:Y|time:Z`
- [ ] `suspended` count > 0
- [ ] `suspended` count < `tabs` count (some tabs protected)
- [ ] Browser remains open (not closed)
- [ ] Pinned tabs NOT suspended
- [ ] Active tab NOT suspended
- [ ] Other tabs appear as "Suspended" or "Discarded"

**Click suspended tab**:
- [ ] Tab reloads automatically
- [ ] Page content loads correctly
- [ ] No errors or broken functionality

### Test 2: Protected Tab Verification

**Setup**:
1. Open Chrome with 5 tabs
2. Pin all 5 tabs
3. Make one tab active

**Execute**:
```bash
uv run scripts/tab_suspender.py --suspend --browser=chrome
```

**Verify**:
- [ ] Output shows: `suspended:0` (all tabs protected)
- [ ] No tabs suspended (all remain active)
- [ ] No errors reported

**Additional Test - Audible Tab**:
1. Play a video on YouTube (with audio)
2. Switch to another tab
3. Run suspension

**Verify**:
- [ ] Tab with audio NOT suspended
- [ ] Other inactive tabs suspended

### Test 3: Integration with Optimizer (Dry Run)

```bash
uv run scripts/optimize.py --dry-run
```

**Verify**:
- [ ] Optimizer starts successfully
- [ ] Analysis phase completes
- [ ] "browser_tab_suspension" appears in optimization list
- [ ] Risk level: "safe"
- [ ] Estimated recovery > 0 MB
- [ ] Description mentions "Extension 사용, 브라우저는 유지"
- [ ] No actual suspension happens (dry run)

### Test 4: Integration with Optimizer (Real Execution)

**Setup**:
1. Open Chrome with 15+ tabs
2. Pin 1-2 tabs
3. Keep one tab active

**Execute**:
```bash
uv run scripts/optimize.py --auto-approve --risk-tolerance=safe
```

**Verify Analysis Phase**:
- [ ] "🔍 시스템 분석 중..." appears
- [ ] "browser_tab_suspension" listed as first optimization
- [ ] Estimated recovery shown

**Verify Execution Phase**:
- [ ] "⚡ 실행 중: browser_tab_suspension" appears
- [ ] Tab suspension executes
- [ ] "✅ 완료: X/Y개 탭 일시중단" appears
- [ ] Browser remains open
- [ ] Inactive tabs suspended

**Verify Summary**:
- [ ] Success count includes tab suspension
- [ ] Total recovery MB includes tab suspension contribution
- [ ] TOON format summary printed

### Test 5: Graceful Degradation (No Extension)

**Setup**:
1. Disable extension in `chrome://extensions/`
2. Or uninstall extension temporarily

**Execute**:
```bash
uv run scripts/optimize.py --dry-run
```

**Verify**:
- [ ] Optimizer runs successfully
- [ ] "browser_tab_suspension" NOT in optimization list (extension not available)
- [ ] Other optimizations still listed
- [ ] No errors or crashes
- [ ] Browser still protected by BLACKLIST

---

## Error Handling Testing

### Test 6: Connection Timeout

**Setup**:
1. Disable extension in Chrome
2. DO NOT uninstall (manifest still exists)

**Execute**:
```bash
uv run scripts/tab_suspender.py --suspend --browser=chrome
```

**Verify**:
- [ ] Command times out (30 seconds max)
- [ ] Error message indicates connection failure
- [ ] Suggests checking extension installation

### Test 7: Extension Not Installed

**Setup**:
1. Remove Native Messaging manifest: `rm ~/.moai/bin/com.moai.tab_suspender.json`
2. Remove Chrome symlink: `rm ~/Library/Application\ Support/Google/Chrome/NativeMessagingHosts/com.moai.tab_suspender.json`

**Execute**:
```bash
uv run scripts/optimize.py --dry-run
```

**Verify**:
- [ ] "browser_tab_suspension" NOT listed (extension not detected)
- [ ] Optimizer continues with other optimizations
- [ ] No crashes or errors

**Cleanup**:
```bash
cd extensions/chrome-tab-suspender
./install.sh  # Reinstall
```

### Test 8: Browser BLACKLIST Protection

**Execute**:
```bash
uv run scripts/process_analyzer_uv.py --format=json
```

**Verify**:
- [ ] Browser processes detected
- [ ] Browser processes NOT flagged for termination
- [ ] Browser memory usage reported
- [ ] No recommendations to close browser

---

## Performance Testing

### Test 9: Memory Recovery Measurement

**Setup**:
1. Open Chrome with 50+ tabs (use extension like "Tab Session Manager")
2. Note current memory usage:
   ```bash
   uv run scripts/analyze_memory.py --format=json
   ```
3. Record "used_percent" value

**Execute**:
```bash
uv run scripts/optimize.py --auto-approve --risk-tolerance=safe
```

**Verify**:
- [ ] Tab suspension executes
- [ ] Wait 10 seconds for memory to stabilize
- [ ] Check memory again:
   ```bash
   uv run scripts/analyze_memory.py --format=json
   ```
- [ ] "used_percent" decreased by 2-5%
- [ ] Recovery aligns with estimated recovery

### Test 10: Execution Time

**Execute with time measurement**:
```bash
time uv run scripts/tab_suspender.py --suspend --browser=chrome
```

**Verify**:
- [ ] Total time < 5 seconds
- [ ] Connection setup < 1 second
- [ ] Tab suspension < 3 seconds
- [ ] Result reporting < 500ms

---

## Integration Testing

### Test 11: Quick Optimize Command

```bash
/macos-resource-optimizer:quick-optimize
```

**Verify**:
- [ ] Command executes successfully
- [ ] Tab suspension included in workflow
- [ ] Browser remains open throughout
- [ ] Memory optimization completes
- [ ] Final report shows tab suspension results

### Test 12: Full Optimize Command

```bash
/macos-resource-optimizer:full-optimize
```

**Verify**:
- [ ] All 6 category analyses run
- [ ] Memory analysis includes browser tab detection
- [ ] Tab suspension recommended if browsers detected
- [ ] Execution phase suspends tabs
- [ ] Browser remains in BLACKLIST (never closed)

---

## Regression Testing

### Test 13: No Breaking Changes to Existing Workflow

**Execute old workflow** (without tab suspension):
```bash
# Remove extension temporarily
uv run scripts/optimize.py --dry-run
```

**Verify**:
- [ ] All existing optimizations still work
- [ ] swap_purge still listed
- [ ] browser_helper_cleanup still listed
- [ ] inactive_app_suspension still listed
- [ ] No errors from missing tab suspension

### Test 14: BLACKLIST Still Enforced

**Execute**:
```bash
uv run scripts/process_analyzer_uv.py
```

**Verify BLACKLIST protection**:
- [ ] Ghostty NEVER recommended for closure
- [ ] VS Code NEVER recommended for closure
- [ ] Chrome NEVER recommended for closure
- [ ] Firefox NEVER recommended for closure
- [ ] Safari NEVER recommended for closure
- [ ] Dia NEVER recommended for closure
- [ ] All browser variants protected

---

## Documentation Testing

### Test 15: README Completeness

Read: `extensions/chrome-tab-suspender/README.md`

- [ ] Installation instructions clear
- [ ] Testing steps detailed
- [ ] Troubleshooting section helpful
- [ ] File structure documented
- [ ] Configuration examples provided
- [ ] Performance metrics realistic

### Test 16: Code Comments

Review code files:

**manifest.json**:
- [ ] All fields documented in README

**background.js**:
- [ ] Functions have JSDoc comments
- [ ] Logic is clear and commented

**tab_suspender.py**:
- [ ] Docstrings for all functions
- [ ] Usage examples in header
- [ ] Protocol documented (Native Messaging)

**install.sh**:
- [ ] Each step numbered and explained
- [ ] Error messages clear
- [ ] Success messages informative

---

## User Acceptance Testing

### Test 17: End-to-End User Flow

**Scenario**: First-time user wants to free memory without losing browser tabs

**Steps**:
1. User runs: `./extensions/chrome-tab-suspender/install.sh`
   - [ ] Installation completes without errors
   - [ ] User understands what to do at each step

2. User runs: `/macos-resource-optimizer:quick-optimize`
   - [ ] Tab suspension automatically included
   - [ ] User sees clear feedback about tabs suspended
   - [ ] Browser remains open (user satisfied)

3. User clicks suspended tab
   - [ ] Tab reloads smoothly
   - [ ] No confusion or errors

4. User checks memory
   - [ ] Memory usage decreased
   - [ ] User satisfied with result

**Overall**:
- [ ] User never lost work
- [ ] User never confused
- [ ] User satisfied with outcome

---

## Final Validation

### MVP Completion Checklist

- [ ] All 17 tests passed
- [ ] No critical bugs found
- [ ] Performance meets expectations (< 5s execution)
- [ ] Memory recovery meets expectations (200-500 MB typical)
- [ ] Documentation complete and accurate
- [ ] Integration with optimizer seamless
- [ ] BLACKLIST protection maintained
- [ ] User experience smooth

### Phase 1 Sign-Off

- [ ] User tested successfully
- [ ] Ready for daily use
- [ ] No blockers for Phase 2
- [ ] Feedback collected

---

## Troubleshooting Quick Reference

**Issue**: Extension not connecting
- **Fix**: Restart Chrome, run `./install.sh` again

**Issue**: 0 tabs suspended
- **Check**: Are all tabs pinned or active?
- **Expected**: This is normal if all tabs protected

**Issue**: Permission denied
- **Fix**: `chmod +x scripts/tab_suspender.py`

**Issue**: UV not found
- **Fix**: Install UV: `curl -LsSf https://astral.sh/uv/install.sh | sh`

**Issue**: Timeout after 30 seconds
- **Check**: Extension enabled? `chrome://extensions/`
- **Fix**: Disable and re-enable extension

---

**Testing Status**: ⏳ Pending User Validation
**Phase**: 1 (MVP)
**Next**: User acceptance testing and Phase 2 planning
