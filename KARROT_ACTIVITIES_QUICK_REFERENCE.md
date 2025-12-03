# Karrot App Activities - Quick Reference Card

## All Activities at a Glance

| # | Activity Name | Full Class Name | Type | Purpose |
|---|---|---|---|---|
| 1 | **LauncherActivity** | `com.towneers.www.launcher.LauncherActivity` | Entry | App entry point, splash screen |
| 2 | **GuideActivity** | `com.towneers.www.guide.GuideActivity` | Onboarding | Phone verification, welcome |
| 3 | **JpSignUpActivity** | `com.towneers.www.account.entry.jp.JpSignUpActivity` | Auth | Phone login, SMS OTP |
| 4 | **DeepLinkActivity** | `com.towneers.www.deeplink.DeepLinkActivity` | Nav | `karrot://` protocol handler |
| 5 | **AppLinkActivity** | `com.towneers.www.applink.AppLinkActivity` | Nav | `https://karrot.co.kr` handler |
| 6 | **OneLinkActivity** | `com.towneers.www.appsflyer.OneLinkActivity` | Marketing | AppsFlyer link handler |
| 7 | **ArticleDetailActivity** | `com.towneers.www.article.detail.presentation.ArticleDetailActivity` | Content | Display marketplace items |
| 8 | **ProfileEntryActivity** | `com.towneers.www.profileentry.ProfileEntryActivity` | Profile | User profile & listings |
| 9 | **EffectOneExportActivity** | `com.karrot.www.videoeditor.byteplus.export.EffectOneExportActivity` | Video | Video editing (BytePlus) |
| 10 | **LineAuthenticationCallbackActivity** | `com.linecorp.linesdk.auth.internal.LineAuthenticationCallbackActivity` | Auth | LINE OAuth callback |

---

## Critical Path Activities (For Automation)

### Phase 1: Launch & Check
```
LauncherActivity (5-10s)
  ├─ Play Integrity API check
  ├─ Load cached state
  └─ Transition: → GuideActivity
```

### Phase 2: Onboarding
```
GuideActivity (Variable)
  ├─ Phone verification check
  ├─ Location permission request
  ├─ Terms acceptance
  └─ Transition: → JpSignUpActivity
```

### Phase 3: Phone Login
```
JpSignUpActivity (15-30s)
  ├─ Phone number input (410, 254) @ 1440x2560
  ├─ SMS OTP verification
  ├─ Confirm button (720, 2520) @ 1440x2560
  └─ Transition: → Main Feed/Home
```

---

## Intent Commands for Direct Access

### Launch Entry Point
```bash
adb shell am start -n com.towneers.www/.launcher.LauncherActivity
```

### Skip to Signup (Faster Testing)
```bash
adb shell am start -n com.towneers.www/.account.entry.jp.JpSignUpActivity
```

### Navigate via Deep Links
```bash
# Article listing
adb shell am start -a android.intent.action.VIEW -d "karrot://article/ID"

# User profile  
adb shell am start -a android.intent.action.VIEW -d "karrot://profile/USER_ID"

# Via HTTPS
adb shell am start -a android.intent.action.VIEW -d "https://www.karrot.co.kr/article/ID"
```

---

## Detection & Bypass Status

### Detection Points
| Activity | Detection Type | Error | Solution |
|----------|---|---|---|
| LauncherActivity | Play Integrity API | -18 | PlayIntegrityFork module |
| JpSignUpActivity | LIAPP security | Block | Shamiko + HideMyApplist |
| All Activities | Build.prop checks | Crash | Device fingerprint spoof |

### Bypass Setup
```
Required:
  ✓ Magisk v26+ with Zygisk
  ✓ PlayIntegrityFork module
  ✓ Shamiko module
  
Optional:
  ○ HideMyApplist module
  ○ Device fingerprint customization
```

---

## UI Coordinates (1440x2560 Resolution)

### Login Screen (JpSignUpActivity)
- **Phone Input Field**: X=410, Y=254
- **Confirm Button**: X=720, Y=2520  
- **Back Button**: X=40, Y=56

---

## Activity Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ App Launch (Home Screen Tap)                                │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ LauncherActivity     │ ◄─── ENTRY POINT
        │ (5-10 seconds)       │
        └──────────┬───────────┘
                   │ Play Integrity Check
                   │
        ┌──────────▼───────────┐
        │ GuideActivity        │ ◄─── ONBOARDING
        │ (Variable duration)  │
        └──────────┬───────────┘
                   │ User proceeds
                   │
        ┌──────────▼───────────────────────┐
        │ JpSignUpActivity                 │ ◄─── PHONE LOGIN
        │ Phone: (410, 254)                │
        │ Button: (720, 2520)              │
        └──────────┬──────────────────────┘
                   │ SMS OTP verified
                   │
        ┌──────────▼───────────┐
        │ Main Feed / Home     │ ◄─── MARKETPLACE
        │ (Hidden in dumpsys)  │
        └──────────┬───────────┘
                   │
        ┌──────────▼──────────────────────┐
        │ User Navigation:                 │
        ├──────────────────────────────────┤
        │ ├─ Tap Article → ArticleDetail   │
        │ ├─ Tap User → ProfileEntry       │
        │ ├─ Link (karrot://) → DeepLink   │
        │ ├─ Link (https://) → AppLink     │
        │ └─ AppsFlyer → OneLink           │
        └──────────────────────────────────┘
```

---

## Monitoring Commands

### Watch Activity Transitions
```bash
adb logcat -c
adb shell am start -n com.towneers.www/.launcher.LauncherActivity
adb logcat -d | grep -E "ActivityRecord|START.*com.towneers"
```

### Check Detection Status
```bash
adb logcat | grep -iE "error.*18|PlayIntegrity|LIAPP|root|magisk"
```

### Get Full Activity Dump
```bash
adb shell dumpsys package com.towneers.www | grep Activity
```

### See Current Foreground Activity
```bash
adb shell dumpsys activity | grep mFocusedApp
```

---

## Permissions Required

| Activity | Permissions |
|----------|---|
| LauncherActivity | None |
| GuideActivity | ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION |
| JpSignUpActivity | RECEIVE_SMS, READ_SMS, SEND_SMS |
| ArticleDetailActivity | CAMERA, READ_EXTERNAL_STORAGE |
| ProfileEntryActivity | READ_CONTACTS, ACCESS_FINE_LOCATION |

---

## Key Technical Details

**Package**: `com.towneers.www`
**APK Size**: 95.4 MB
**Min SDK**: Android 7.0+
**Detection Framework**: Play Integrity API + LIAPP
**Video Processing**: BytePlus EffectOne
**Authentication**: Phone OTP + LINE OAuth

---

## Files Reference

📄 **KARROT_ACTIVITIES_MAP.md** - Full comprehensive documentation (589 lines)
📄 **KARROT_ACTIVITIES_SUMMARY.txt** - Summary with all key info (290 lines)
📄 **KARROT_ACTIVITIES_QUICK_REFERENCE.md** - This file (Quick lookup)

---

**Last Updated**: 2025-12-03
**Device**: BlueStacks Air (1440x2560)
**Confidence**: HIGH
