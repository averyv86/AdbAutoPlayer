#!/bin/bash
# Test Phase 2 RAM Agents 1-2 Click CLI Integration

echo "=== Testing Phase 2 RAM Agents 1-2 ==="
echo ""

# Test agent_memory_pressure_detector.py
echo "1. Testing agent_memory_pressure_detector.py..."
echo "   Format: JSON"
if uv run agent_memory_pressure_detector.py --format json | python3 -c "import sys, json; json.load(sys.stdin)" 2>/dev/null; then
    echo "   ✅ JSON output valid"
else
    echo "   ❌ JSON output invalid"
    exit 1
fi

echo "   Format: Summary"
uv run agent_memory_pressure_detector.py --format summary
echo ""

# Test agent_app_memory_profiler.py
echo "2. Testing agent_app_memory_profiler.py..."
echo "   Format: JSON"
if uv run agent_app_memory_profiler.py --format json | python3 -c "import sys, json; json.load(sys.stdin)" 2>/dev/null; then
    echo "   ✅ JSON output valid"
else
    echo "   ❌ JSON output invalid"
    exit 1
fi

echo "   Format: Summary"
uv run agent_app_memory_profiler.py --format summary
echo ""

# Test verbose mode
echo "3. Testing verbose mode..."
echo "   Memory Pressure Detector (verbose JSON)"
VERBOSE_OUTPUT=$(uv run agent_memory_pressure_detector.py --format json --verbose)
if echo "$VERBOSE_OUTPUT" | python3 -c "import sys, json; data = json.load(sys.stdin); exit(0 if len(data.get('recommendations', [])) > 3 else 1)"; then
    echo "   ✅ Verbose mode includes full recommendations"
else
    echo "   ⚠️  Verbose mode may not include all recommendations"
fi

echo ""
echo "4. Testing execution time tracking..."
TIME_DATA=$(uv run agent_memory_pressure_detector.py --format json | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['execution_time_ms'])")
if (( $(echo "$TIME_DATA > 0" | bc -l) )); then
    echo "   ✅ Execution time tracked: ${TIME_DATA}ms"
else
    echo "   ❌ Execution time not tracked"
    exit 1
fi

echo ""
echo "5. Testing coordinator-compatible fields..."
JSON_OUTPUT=$(uv run agent_app_memory_profiler.py --format json)
REQUIRED_FIELDS="agent zombies_found total_memory_bytes execution_time_ms pids"
ALL_PRESENT=true
for field in $REQUIRED_FIELDS; do
    if echo "$JSON_OUTPUT" | python3 -c "import sys, json; data = json.load(sys.stdin); exit(0 if '$field' in data else 1)"; then
        echo "   ✅ Field '$field' present"
    else
        echo "   ❌ Field '$field' missing"
        ALL_PRESENT=false
    fi
done

if [ "$ALL_PRESENT" = true ]; then
    echo ""
    echo "✅ All tests passed! Phase 2 agents 1-2 are coordinator-compatible."
    exit 0
else
    echo ""
    echo "❌ Some tests failed. Please review the output above."
    exit 1
fi
