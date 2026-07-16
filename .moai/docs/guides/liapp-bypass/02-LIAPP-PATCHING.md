# Part 2: smali Patching

> **Quick Reference** - Essential commands for LIAPP bypass patching

---

## Prerequisites

```bash
# Install tools (macOS)
brew install apktool
brew install openjdk

# Verify
apktool --version
java -version
```

---

## Step 1: Decompile APK

```bash
# Create work directory
mkdir -p /tmp/karrot-patch && cd /tmp/karrot-patch

# Extract APK from device
adb shell pm path com.towneers.www
adb pull /data/app/~~xxx/base.apk karrot.apk

# Decompile
apktool d karrot.apk -o karrot-apk
```

---

## Step 2: Locate Target File

```bash
# Find LIAPP smali file
find karrot-apk -name "*.smali" -path "*lockincomp*"

# Target: smali_classes5/com/lockincomp/wfcwxdz/ꪶꪻ.smali
```

---

## Step 3: Patch Termination Method

**Find this method**: `حسۭݴ߰(I)V`

### Original Code
```smali
.method public حسۭݴ߰(I)V
    .registers 3

    new-instance p1, Ljava/lang/RuntimeException;
    invoke-direct {p1}, Ljava/lang/RuntimeException;-><init>()V
    throw p1
.end method
```

### Patched Code
```smali
.method public حسۭݴ߰(I)V
    .registers 3

    # PATCHED: Return instead of throw
    return-void

    # Original code commented out:
    # new-instance p1, Ljava/lang/RuntimeException;
    # invoke-direct {p1}, Ljava/lang/RuntimeException;-><init>()V
    # throw p1
.end method
```

---

## Step 4: Add Native Method Declaration

If native method `ڳִٯڮܪ` is missing declaration:

```smali
# Add before .end class
.method public static native ڳִٯڮܪ()V
.end method
```

---

## Step 5: Rebuild APK

```bash
# Rebuild
apktool b karrot-apk -o karrot-patched.apk

# Check output
ls -la karrot-patched.apk
```

---

## Quick Patch Script

```bash
#!/bin/bash
# patch-liapp.sh

SMALI_FILE="karrot-apk/smali_classes5/com/lockincomp/wfcwxdz/ꪶꪻ.smali"

# Backup
cp "$SMALI_FILE" "$SMALI_FILE.bak"

# Patch: Replace throw with return-void
sed -i '' 's/throw p1/return-void/g' "$SMALI_FILE"

echo "Patched: $SMALI_FILE"
```

---

## Verification

```bash
# Check patch applied
grep -A5 "حسۭݴ߰" karrot-apk/smali_classes5/com/lockincomp/wfcwxdz/ꪶꪻ.smali

# Should see return-void instead of throw
```

---

## Common Errors

| Error | Solution |
|-------|----------|
| `brut.androlib.AndrolibException` | Update apktool: `brew upgrade apktool` |
| File encoding issues | Use UTF-8: `LANG=en_US.UTF-8` |
| Missing resources | Add `--use-aapt2` flag |
