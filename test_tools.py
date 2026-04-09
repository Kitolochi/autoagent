"""Quick test of Premiere and AE tools"""
import asyncio
import sys
sys.path.insert(0, '/c/Users/chris/autoagent')

from tools.premiere import get_project_info, get_active_sequence, apply_lut, add_keyframe
from tools.aftereffects import create_ae_composition, run_ae_script

async def test_premiere():
    print("\n=== Testing Premiere Pro Tools ===")
    
    # Test 1: Basic read
    print("\n1. get_project_info:")
    result = await get_project_info()
    print(f"   {result[:200]}")
    
    # Test 2: Get active sequence
    print("\n2. get_active_sequence:")
    result = await get_active_sequence()
    print(f"   {result[:200]}")
    
    # Test 3: Try a new tool (will fail gracefully if no clips)
    print("\n3. apply_lut (testing new tool signature):")
    result = await apply_lut(0, 0, "C:/test.cube")
    print(f"   {result[:200]}")

async def test_ae():
    print("\n\n=== Testing After Effects Tools ===")
    
    # Test 1: Simple script
    print("\n1. run_ae_script (get app version):")
    result = await run_ae_script("app.version;")
    print(f"   {result[:200]}")
    
    # Test 2: Create composition
    print("\n2. create_ae_composition:")
    result = await create_ae_composition("TestComp", 1920, 1080, 30, 5)
    print(f"   {result[:200]}")

async def main():
    try:
        await test_premiere()
    except Exception as e:
        print(f"Premiere test error: {e}")
    
    try:
        await test_ae()
    except Exception as e:
        print(f"AE test error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
