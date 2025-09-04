#!/usr/bin/env python3
"""
Test script for Pixel Inspector functionality.

This script launches the DStretch GUI with the new Pixel Inspector integrated.
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
        """Launch the DStretch GUI with Pixel Inspector."""
        print("Launching DStretch Python with Pixel Inspector...")
        print("New features:")
        print("  • Real-time pixel analysis")
        print("  • RGB, HSV, LAB color spaces")
        print("  • Freeze/unfreeze values")
        print("  • Copy to clipboard")
        print("  • Sampling sizes: 1x1, 3x3, 5x5")
        print()
        
        app = DStretchGUI()
        app.run()
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"Error importing DStretch modules: {e}")
    print("Please make sure you're running from the dstretch_python directory")
    sys.exit(1)
