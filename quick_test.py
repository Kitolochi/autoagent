"""Quick verification test for Premiere and AE"""
import asyncio
import json
import sys
from tools.premiere import _call_tool
from tools.aftereffects import _call_tool as ae_call_tool

async def main():
    print('=== Quick Verification Test ===\n')
    passed = 0
    total = 2

    # Test 1: Premiere (read-only)
    print('1. Premiere Pro:')
    try:
        result = await _call_tool('get_project_info', {})
        if 'ERROR' in result or 'error' in result.lower():
            print(f'   [FAIL] {result[:100]}')
        else:
            data = json.loads(result)
            print(f'   [PASS] Project: {data.get("name", "Unknown")}')
            passed += 1
    except Exception as e:
        print(f'   [FAIL] {str(e)[:100]}')

    # Test 2: After Effects
    print('\n2. After Effects:')
    try:
        result = await ae_call_tool('run-script', {'script': 'app.version;', 'timeout': 10000})
        if 'ERROR' in result or 'timed out' in result.lower():
            print(f'   [FAIL] {result[:100]}')
        else:
            print(f'   [PASS] Result: {result[:80]}')
            passed += 1
    except Exception as e:
        print(f'   [FAIL] {str(e)[:100]}')

    print(f'\n=== {passed}/{total} platforms verified ===')
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
