# Part 1: LIAPP Analysis

> **Quick Reference** - Key findings for LIAPP SDK bypass

---

## LIAPP SDK Overview

**Vendor**: Lockin Company (Korea)
**Purpose**: Mobile app security (anti-tampering, root detection, debugging prevention)

---

## Detection Method

### 1. Find LIAPP Package
```bash
# In decompiled APK, search for:
grep -r "lockincomp\|liapp" smali_classes*/

# Karrot uses obfuscated package:
com.lockincomp.wfcwxdz
```

### 2. Locate Key Classes
```bash
ls smali_classes5/com/lockincomp/wfcwxdz/

# Look for classes with Unicode names (obfuscated):
ꪶꪻ.smali    # Main security class
```

---

## Key Class Structure

**File**: `smali_classes5/com/lockincomp/wfcwxdz/ꪶꪻ.smali`

```java
// Decompiled structure (JADX)
public class ꪶꪻ {
    // Native method - security check
    public static native void ڳִٯڮܪ();

    // Termination method - kills app on detection
    public void حسۭݴ߰(int) {
        throw new RuntimeException();  // <-- PATCH THIS
    }
}
```

---

## Security Mechanisms

| Check | Description | Bypass Method |
|-------|-------------|---------------|
| Root Detection | Checks for su, Magisk | Hide with Shamiko/DenyList |
| Integrity Check | Verifies APK signature | Patch termination method |
| Debugger Detection | Checks TracerPid | Not critical for automation |
| Emulator Detection | Checks build properties | BlueStacks Air passes |

---

## Critical Method

**`حسۭݴ߰(I)V`** - Called when security violation detected

```
Input: int (violation code)
Action: throws RuntimeException → app crashes
Target: Patch to return-void instead of throw
```

---

## Native Library

```bash
# Check for native security libs
ls lib/arm64-v8a/

# LIAPP may use:
# - libLIAPP.so (explicit)
# - lib*.so with obfuscated names
```

---

## Analysis Tools

| Tool | Purpose |
|------|---------|
| `apktool` | Decompile/recompile APK |
| `JADX` | Java decompilation (read-only) |
| `grep` | Search smali for patterns |

---

## Identifying LIAPP in Other Apps

```bash
# Step 1: Check for lockincomp package
unzip -l app.apk | grep -i lockin

# Step 2: Search smali for RuntimeException in security context
grep -r "RuntimeException" smali_classes*/ | grep -v test

# Step 3: Look for obfuscated class names (Unicode)
find smali_classes*/ -name "*.smali" | xargs file | grep -i unicode
```
