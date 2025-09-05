#!/usr/bin/env python3
"""
Simple test for DStretch Python v2.0 imports
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    print("Testing basic import...")
    import dstretch
    print("✅ Basic import successful")
    
    print("Testing pipeline info...")
    info = dstretch.get_pipeline_info()
    print("✅ Pipeline info:", info)
    
    print("Testing colorspaces...")
    colorspaces = dstretch.list_available_colorspaces()
    print(f"✅ Found {len(colorspaces)} colorspaces")
    
    print("Testing processors...")
    processors = dstretch.get_available_processors()
    print(f"✅ Found {len(processors)} processors")
    
    print("Testing pipeline creation...")
    pipeline = dstretch.create_dstretch_pipeline()
    print("✅ Pipeline created successfully")
    
    print("\n🎉 ALL IMPORTS SUCCESSFUL!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
