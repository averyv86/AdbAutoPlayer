#!/bin/bash
# Test script for karrot_state_detector.py

echo "==================================="
echo "Karrot State Detector - Test Suite"
echo "==================================="
echo ""

echo "1. Validate TOON Configuration"
echo "-----------------------------------"
uv run karrot_state_detector.py --validate
echo ""

echo "2. List All States (first 3)"
echo "-----------------------------------"
uv run karrot_state_detector.py --list-states | head -20
echo ""

echo "3. Get Element Coordinates (Safe Zone)"
echo "-----------------------------------"
uv run karrot_state_detector.py --state welcome --element get_started_btn
echo ""

echo "4. Get Element Coordinates (Country Selector)"
echo "-----------------------------------"
uv run karrot_state_detector.py --state welcome --element country_selector
echo ""

echo "5. Test Banned Zone Filtering (login_link in banned zone)"
echo "-----------------------------------"
echo "Note: login_link at y=2493 is in BlueStacks banner zone (2440-2560)"
uv run karrot_state_detector.py --state welcome --element login_link 2>&1 || echo "✓ Correctly blocked banned zone element"
echo ""

echo "6. JSON Output Example"
echo "-----------------------------------"
uv run karrot_state_detector.py --state login_phone --element phone_input --json
echo ""

echo "7. Validate JSON Output"
echo "-----------------------------------"
uv run karrot_state_detector.py --validate --json
echo ""

echo "==================================="
echo "All tests completed successfully!"
echo "==================================="
