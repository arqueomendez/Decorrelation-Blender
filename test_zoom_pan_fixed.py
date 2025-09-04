#!/usr/bin/env python3
"""
Test script for FIXED Zoom & Pan functionality.

This script launches the DStretch GUI with the corrected Zoom & Pan controls.
"""

import sys
from pathlib import Path

# Add the source directory to Python path
src_path = Path(__file__).parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

try:
    from dstretch.gui import DStretchGUI
    
    def main():
        """Launch the DStretch GUI with FIXED Zoom & Pan."""
        print("🔧 DStretch Python - FIXED Zoom & Pan Controls")
        print("=" * 50)
        print()
        print("✅ FIXED: Drag & Pan now works correctly!")
        print()
        print("🖱️  CORRECTED MOUSE CONTROLS:")
        print("   • Mouse Wheel: Zoom in/out (centered on cursor)")
        print("   • RIGHT-CLICK + DRAG: Pan image around")
        print("   • LEFT-CLICK: Inspector Píxeles (freeze/unfreeze)")
        print("   • SHIFT + LEFT-DRAG: Alternative pan method")
        print()
        print("🔍 ZOOM CONTROLS:")
        print("   • Toolbar: [🔍-] [🔍+] [Fit] [100%] buttons")
        print("   • Dropdown: Direct zoom level selection")
        print("   • Levels: 25%, 50%, 100%, 200%, 400%, 800%")
        print()
        print("🎯 WORKFLOW:")
        print("   1. Load an image (File -> Open)")
        print("   2. Use mouse wheel to zoom in/out")
        print("   3. RIGHT-CLICK and drag to pan around")
        print("   4. LEFT-CLICK for pixel inspection")
        print("   5. Use toolbar buttons for quick navigation")
        print()
        print("🚀 Starting DStretch...")
        print()
        
        app = DStretchGUI()
        app.run()
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Error importing DStretch modules: {e}")
    print("Please make sure you're running from the dstretch_python directory")
    sys.exit(1)
