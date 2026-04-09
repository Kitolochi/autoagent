"""Quick verification test for Premiere and AE"""
import asyncio
import sys
from tools.premiere import _call_tool
from tools.aftereffects import _call_tool as ae_call_tool

async def main():
    print('=== Quick Verification Test ===\n')

    # Test 1: Premiere (read-only)
    print('1. Premiere Pro:')
    try:
        result = await _call_tool('get_project_info', {})
        if 'ERROR' in result or 'error' in result.lower():
            print(f'   [FAIL] Not working: {result[:100]}')
            return 1
        else:
            # Parse project name
            import json
            data = json.loads(result)
            print(f'   [PASS] WORKING! Project: {data.get("name", "Unknown")}')
    except Exception as e:
        print(f'   [FAIL] Error: {str(e)[:100]}')
        return 1

    # Test 2: After Effects
    print('\n2. After Effects:')
    try:
        result = await ae_call_tool('run-script', {'script': 'app.version;', 'timeout': 10000})
        if 'ERROR' in result or 'timed out' in result.lower():
            print(f'   [FAIL] Not working: {result[:100]}')
            print('   --> Did you restart the bridge? (Stop -> Start)')
            return 1
        else:
            print(f'   [PASS] WORKING! Result: {result[:80]}')
    except Exception as e:
        print(f'   [FAIL] Error: {str(e)[:100]}')
        return 1

    print('\n=== [PASS] Both platforms verified! ===')
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
