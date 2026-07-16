# Part 3: APK Signing & Installation

> **Quick Reference** - Essential commands for signing and installing patched APK

---

## Step 1: Create Keystore (One-time)

```bash
keytool -genkey -v \
  -keystore my.keystore \
  -alias mykey \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000

# Follow prompts (remember password!)
# Store keystore safely
```

---

## Step 2: Sign APK

```bash
# Sign with jarsigner
jarsigner -verbose \
  -sigalg SHA256withRSA \
  -digestalg SHA-256 \
  -keystore my.keystore \
  karrot-patched.apk \
  mykey

# Verify signature
jarsigner -verify karrot-patched.apk
```

---

## Step 3: Uninstall Original

```bash
# Must uninstall first (signature mismatch)
adb uninstall com.towneers.www
```

---

## Step 4: Install Patched APK

```bash
# Install
adb install karrot-patched.apk

# Or with replacement flag (if already uninstalled)
adb install -r karrot-patched.apk
```

---

## Step 5: Verify Installation

```bash
# Check installed
adb shell pm list packages | grep towneers

# Check version
adb shell dumpsys package com.towneers.www | grep versionName

# Launch app
adb shell monkey -p com.towneers.www -c android.intent.category.LAUNCHER 1
```

---

## All-in-One Command

```bash
# Complete signing and installation
apktool b karrot-apk -o karrot-patched.apk && \
jarsigner -keystore my.keystore karrot-patched.apk mykey && \
adb uninstall com.towneers.www && \
adb install karrot-patched.apk
```

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| `INSTALL_FAILED_UPDATE_INCOMPATIBLE` | Uninstall first: `adb uninstall com.towneers.www` |
| `INSTALL_FAILED_NO_MATCHING_ABIS` | Wrong architecture, use arm64-v8a APK |
| `Failure [INSTALL_PARSE_FAILED_NO_CERTIFICATES]` | Sign the APK first |
| Keystore password forgotten | Create new keystore |

---

## Optional: zipalign (Performance)

```bash
# Find zipalign (Android SDK)
find ~/Library/Android -name "zipalign" 2>/dev/null

# Align before signing
zipalign -v 4 karrot-patched.apk karrot-aligned.apk

# Then sign aligned APK
jarsigner -keystore my.keystore karrot-aligned.apk mykey
```

---

## File Locations

| File | Path |
|------|------|
| Keystore | `./my.keystore` (keep safe!) |
| Patched APK | `/tmp/karrot-patch/karrot-patched.apk` |
| Final APK | `/tmp/karrot-patch/karrot-v11-final.apk` |
