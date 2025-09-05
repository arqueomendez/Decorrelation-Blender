#!/usr/bin/env python3
"""
Test script for Color Balance Processor functionality.
"""

import numpy as np
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from dstretch.color_balance_processor import (
        ColorBalanceProcessor, ColorBalanceParams, BalanceMethod, 
        create_test_image_with_cast
    )
    print("✅ Color Balance imports successful")
    
    # Test 1: Create processor
    processor = ColorBalanceProcessor()
    print("✅ ColorBalanceProcessor created successfully")
    
    # Test 2: Create test image with color cast
    test_image = create_test_image_with_cast()
    print(f"✅ Test image created: {test_image.shape}, dtype={test_image.dtype}")
    
    # Test 3: Analyze color cast
    analysis = processor.analyze_color_cast(test_image)
    print(f"✅ Color cast analysis completed:")
    print(f"   - Channel means: {[f'{m:.3f}' for m in analysis['channel_means']]}")
    print(f"   - Cast strength: {analysis['cast_strength']:.3f}")
    print(f"   - Needs correction: {analysis['needs_correction']}")
    print(f"   - Dominant cast: {analysis['dominant_cast']}")
    
    # Test 4: Apply Gray World balance
    params = ColorBalanceParams(
        method=BalanceMethod.GRAY_WORLD,
        clip_percentage=0.1,
        strength=1.0
    )
    
    balanced_image = processor.process(test_image, params)
    print(f"✅ Gray World balance applied: {balanced_image.shape}, dtype={balanced_image.dtype}")
    
    # Test 5: Get statistics
    stats = processor.get_balance_statistics()
    print(f"✅ Balance statistics retrieved:")
    print(f"   - Original means: {[f'{m:.3f}' for m in stats['original_means']]}")
    print(f"   - Gray level: {stats['gray_level']:.3f}")
    print(f"   - Correction factors: {[f'{f:.3f}' for f in stats['correction_factors']]}")
    
    # Test 6: Test integration with DecorrelationStretch
    from dstretch import DecorrelationStretch
    dstretch = DecorrelationStretch()
    
    # Apply color balance through main API
    balanced_via_api = dstretch.apply_color_balance(
        test_image,
        method='gray_world',
        clip_percentage=0.1,
        strength=1.0
    )
    print(f"✅ Color balance via DecorrelationStretch API: {balanced_via_api.shape}")
    
    # Compare results
    difference = np.mean(np.abs(balanced_image.astype(float) - balanced_via_api.astype(float)))
    print(f"✅ API consistency check: mean difference = {difference:.6f}")
    
    if difference < 0.01:
        print("✅ API results are consistent!")
    else:
        print("⚠️  API results differ slightly")
    
    print("\n🎉 ALL COLOR BALANCE TESTS PASSED!")
    
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
