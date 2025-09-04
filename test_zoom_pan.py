#!/usr/bin/env python3
"""
Test script for Zoom & Pan functionality.

This script launches the DStretch GUI with the new Zoom & Pan capabilities.
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
        """Launch the DStretch GUI with Zoom & Pan."""
        print("Launching DStretch Python with Zoom & Pan...")
        print("New features added:")
        print("  ✅ Inspector píxeles básico")
        print("  ✅ Zoom & Pan interactivos")
        print()
        print("Zoom & Pan Controls:")
        print("  • Mouse Wheel: Zoom in/out centered on cursor")
        print("  • Drag: Pan image around")
        print("  • Toolbar: Zoom In/Out, Fit, 100% buttons")
        print("  • Dropdown: Select specific zoom levels")
        print("  • Keyboard: Focus canvas first, then use shortcuts")
        print()
        print("Zoom Levels: 25%, 50%, 100%, 200%, 400%, 800%")
        print("Integration: Inspector píxeles works with zoom coordinates")
        print()
        
        app = DStretchGUI()
        app.run()
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"Error importing DStretch modules: {e}")
    print("Please make sure you're running from the dstretch_python directory")
    sys.exit(1)
