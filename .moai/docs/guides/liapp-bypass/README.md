# LIAPP Bypass Quick Reference

> **Target App**: Karrot (당근마켓) - `com.towneers.www`
> **LIAPP Version**: SDK with obfuscated package `com.lockincomp.wfcwxdz`
> **Last Updated**: 2025-12-03

---

## Quick Start

```bash
# 1. Extract APK
adb shell pm path com.towneers.www
adb pull /data/app/~~xxx/base.apk karrot.apk

# 2. Decompile
apktool d karrot.apk -o karrot-apk

# 3. Patch (see 02-LIAPP-PATCHING.md)
# Edit: smali_classes5/com/lockincomp/wfcwxdz/ꪶꪻ.smali

# 4. Rebuild & Sign
apktool b karrot-apk -o karrot-patched.apk
jarsigner -keystore my.keystore karrot-patched.apk mykey

# 5. Install
adb install -r karrot-patched.apk
```

---

## Key Files

| File | Purpose |
|------|---------|
| `smali_classes5/com/lockincomp/wfcwxdz/ꪶꪻ.smali` | Main LIAPP class to patch |
| `/tmp/karrot-patch/karrot-v11-final.apk` | Working patched APK (91MB) |

---

## Core Patch

**Method**: `حسۭݴ߰(I)V` - App termination method

```smali
# BEFORE (throws exception)
throw p1

# AFTER (returns safely)
return-void
```

---

## Detection Avoidance

| Setting | Value |
|---------|-------|
| Random Delay | 500-2000ms |
| Tap Variance | ±10px |
| Log Keywords | LIAPP, security, tamper, root, magisk |

---

## Part Index

| Part | Content | Link |
|------|---------|------|
| 1 | LIAPP Analysis | [01-LIAPP-ANALYSIS.md](01-LIAPP-ANALYSIS.md) |
| 2 | smali Patching | [02-LIAPP-PATCHING.md](02-LIAPP-PATCHING.md) |
| 3 | APK Signing | [03-APK-SIGNING.md](03-APK-SIGNING.md) |
| 4 | Automation | [04-AUTOMATION.md](04-AUTOMATION.md) |

---

## UI Coordinates (1440x2560)

| Screen | Element | Coordinates |
|--------|---------|-------------|
| Welcome | Get Started | (720, 2374) |
| Welcome | Log In | (872, 2493) |
| Login | Phone Input | (410, 254) |
| Login | Confirm | (720, 2520) |
| Login | Back | (40, 56) |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| App crashes on launch | Check smali patch is correct |
| Signature mismatch | Uninstall first: `adb uninstall com.towneers.www` |
| LSPosed dialog blocks | `adb shell pm disable-user --user 0 org.lsposed.manager` |
| Activity not exported | Use monkey: `adb shell monkey -p com.towneers.www -c android.intent.category.LAUNCHER 1` |
