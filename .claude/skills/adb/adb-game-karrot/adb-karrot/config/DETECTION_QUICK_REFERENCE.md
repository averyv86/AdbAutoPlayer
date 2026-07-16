# Karrot Screen Detection - Quick Reference Card

## Problem
**KrSignUpOrInActivity** shows 3 different screens. Activity name ALONE is not enough.

## Solution
Use BOTH activity name AND UI elements to detect screens accurately.

---

## Detection Quick Reference Table

| Activity | Screen | Required UI Elements | Absent UI Elements | Confidence |
|----------|--------|----------------------|-------------------|------------|
| **GuideActivity** | Welcome | "Get Started" button | - | 95% |
| **KrSignUpOrInActivity** | Verification Code | Code input + Verify button | Search, Phone | 92% |
| **KrSignUpOrInActivity** | Phone Input | Phone input field | Verification | 90% |
| **KrSignUpOrInActivity** | Neighborhood | Search input field | Verification | 88% |
| **MainActivity** | Home | Feed list OR Sell button | - | 95% |
| **com.android.vending** | Play Store | "Google Play" header | - | 99% |

---

## Quick Command Reference

### Get Current Activity
```bash
adb shell dumpsys activity | grep mCurrentFocus
# Output: mCurrentFocus=Window{xxxxx u0 com.towneers.www/com.towneers.app.intro.KrSignUpOrInActivity}
```

### Dump UI Elements
```bash
adb shell uiautomator dump /dev/stdout
# Output: XML with all visible UI elements
```

### Python Implementation (Minimal)

```python
import subprocess, re, xml.etree.ElementTree as ET

# Get activity
result = subprocess.run(
    "adb shell dumpsys activity | grep mCurrentFocus",
    shell=True, capture_output=True, text=True
)
activity = re.search(r'/([^}]+)', result.stdout).group(1)

# Dump UI
result = subprocess.run(
    "adb shell uiautomator dump /dev/stdout",
    shell=True, capture_output=True, text=True
)
root = ET.fromstring(result.stdout)

# Detect screen
if "GuideActivity" in activity:
    screen = "welcome"

elif "KrSignUpOrInActivity" in activity:
    # Check verification code (most specific)
    buttons = [btn.get('text','') for btn in root.findall('.//android.widget.Button')]
    inputs = [inp.get('hint','') for inp in root.findall('.//android.widget.EditText')]
    
    if any('verify' in b.lower() for b in buttons) and \
       any('verification' in i.lower() or 'code' in i.lower() for i in inputs):
        screen = "verification_code"
    
    # Check phone input
    elif any('phone' in i.lower() or 'number' in i.lower() for i in inputs):
        screen = "login_phone"
    
    # Check neighborhood search
    elif any('search' in i.lower() or 'neighborhood' in i.lower() for i in inputs):
        screen = "neighborhood_search"
    
    else:
        screen = "unknown"

elif "MainActivity" in activity:
    screen = "home"

else:
    screen = "unknown"

print(screen)
```

---

## Detection Flow Chart

```
┌─────────────────────────────────┐
│ Get Current Activity            │
│ (dumpsys activity)              │
└──────────┬──────────────────────┘
           │
           ├─ GuideActivity? ─────────► "welcome"
           │
           ├─ KrSignUpOrInActivity?
           │  │
           │  ├─ Has verification code input + verify button? ──► "verification_code"
           │  │
           │  ├─ Has phone input? ──► "login_phone"
           │  │
           │  ├─ Has search input? ──► "neighborhood_search"
           │  │
           │  └─ UNKNOWN? Use AI Vision ──► try_vision_api()
           │
           ├─ MainActivity? + has feed? ──► "home"
           │
           ├─ com.android.vending? ──► "play_store"
           │
           └─ UNKNOWN ──► use_vision_api()
```

---

## Element Markers (What to Look For)

### Verification Code Screen
- Text input with hint = "verification", "code", "인증", "코드"
- Button with text = "Verify", "Confirm", "인증", "확인", "완료"
- (Optional) Button with text = "Resend", "다시"

### Phone Input Screen
- Text input with hint = "phone", "number", "전화", "번호"
- Dropdown/Spinner with "+82" or "Korea"
- Button with text = "Confirm", "Next", "Continue", "확인", "다음"

### Neighborhood Search Screen
- Text input with hint = "search", "neighborhood", "동네", "검색"
- Button with text = "Search", "Find", "검색"
- (Optional) Button with text = "Find nearby"

### Home Screen
- RecyclerView with resource-id containing "feed"
- OR Button with text = "Sell", "판매"
- OR Bottom navigation with tabs

---

## XML Parsing Tips

```python
# Find by text
xpath = "//android.widget.Button[contains(@text, 'Verify')]"

# Find by hint (EditText)
xpath = "//android.widget.EditText[contains(@hint, 'verification')]"

# Find by resource ID
xpath = "//*[@resource-id='com.towneers.www:id/verify_button']"

# Find by class
xpath = "//android.widget.RecyclerView"

# Practical example
root = ET.fromstring(xml_string)
verify_buttons = root.findall(".//android.widget.Button")
for btn in verify_buttons:
    if "verify" in btn.get("text", "").lower():
        # Found verification button
        coordinates = (btn.get("bounds"))  # "x1,y1,x2,y2"
```

---

## Common Mistakes to Avoid

| Mistake | Fix |
|---------|-----|
| Relying only on activity name | Always check UI elements |
| Not handling case sensitivity | Use `.lower()` for text comparisons |
| Forgetting absent elements | Check that unwanted elements are NOT present |
| Timeout too short | Use 500ms activity + 800ms UI = 1.3s total |
| Not handling loading state | If no feed on MainActivity, wait 2-3 seconds |

---

## When to Use Vision API

- When activity + UI element detection returns "unknown"
- When UI elements are dynamically generated
- When text is non-ASCII (Korean characters might be garbled)
- When screen layout changes between app versions

**Cost**: ~$0.003 per API call

---

## Files to Reference

1. **karrot_screen_detection_patterns.yaml** - Full specification
2. **SCREEN_DETECTION_GUIDE.md** - Detailed implementation guide
3. **karrot_states.toon** - State definitions and coordinates
4. **karrot_smart_detector.py** - Current implementation

---

## Testing Checklist

- [ ] Activity detection returns correct activity name
- [ ] UI dump returns valid XML
- [ ] Can find "Get Started" button on welcome screen
- [ ] Can differentiate between verification and phone input screens
- [ ] Can find feed list on home screen
- [ ] Fallback to vision API when uncertain
- [ ] All screens detected within 2 seconds
- [ ] Confidence scores are realistic (0.88-0.99)

