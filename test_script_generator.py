#!/usr/bin/env python3
"""
Test script to verify the updated KooDynaAutomaticSimulationScriptGenerator
works with both old and new JSON formats
"""

import json
import sys
import os

# Add the project path to sys.path
sys.path.insert(0, '/home/koopark/claude/pyKooCAE/occProject/Generators/KooCAEManager')

from KooDynaAutomaticSimulationScriptGenerator import KooDynaAutomaticSimulationScriptGenerator

def test_old_format():
    """Test with the old JSON format"""
    print("=" * 50)
    print("Testing OLD format (scenarios_2025-10-01T20-05-53-704Z.json)")
    print("=" * 50)
    
    with open('/home/koopark/claude/pyKooCAE/Examples/alldropangles/scenarios_2025-10-01T20-05-53-704Z.json', 'r') as f:
        old_data = json.load(f)
    
    generator = KooDynaAutomaticSimulationScriptGenerator(old_data)
    result = generator.generate_for_all()
    
    print(f"Number of scenarios processed: {len(result)}")
    for i, scenario in enumerate(result):
        print(f"\nScenario {i+1}:")
        print(f"  ID: {scenario['id']}")
        print(f"  Name: {scenario['name']}")
        print(f"  Analysis Type: {scenario['analysisType']}")
        print(f"  Angle Source: {scenario.get('angleSource', 'N/A')}")
        if 'tolerance' in scenario:
            print(f"  Tolerance: {scenario['tolerance']}")
        else:
            print(f"  Tolerance: None (old format)")

def test_new_format():
    """Test with the new JSON format"""
    print("\n" + "=" * 50)
    print("Testing NEW format (scenarios_2025-10-02T10-25-19-529Z.json)")
    print("=" * 50)
    
    with open('/home/koopark/claude/pyKooCAE/Examples/alldropangles/scenarios_2025-10-02T10-25-19-529Z.json', 'r') as f:
        new_data = json.load(f)
    
    generator = KooDynaAutomaticSimulationScriptGenerator(new_data)
    result = generator.generate_for_all()
    
    print(f"Number of scenarios processed: {len(result)}")
    for i, scenario in enumerate(result):
        print(f"\nScenario {i+1}:")
        print(f"  ID: {scenario['id']}")
        print(f"  Name: {scenario['name']}")
        print(f"  Analysis Type: {scenario['analysisType']}")
        print(f"  Angle Source: {scenario.get('angleSource', 'N/A')}")
        if 'tolerance' in scenario:
            print(f"  Tolerance: {scenario['tolerance']}")
        else:
            print(f"  Tolerance: None")
        
        # Check for cumulative-specific fields
        if scenario['analysisType'] == 'fullAngleCumulative':
            print(f"  Cumulative Repeat Count: {scenario.get('cumRepeatCount', 'N/A')}")
            print(f"  Cumulative DOE Count: {scenario.get('cumDOECount', 'N/A')}")
            print(f"  Directions Grid: {scenario.get('cumDirectionsGrid', 'N/A')}")

if __name__ == "__main__":
    try:
        test_old_format()
        test_new_format()
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        print("=" * 50)
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
