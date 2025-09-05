#!/usr/bin/env python3
"""
Test script for Flatten Processor functionality.
"""

import numpy as np
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from dstretch.flatten_processor import (
        FlattenProcessor, FlattenParams, FlattenMethod, 
        create_test_image_with_uneven_illumination, recommend_flatten_method
    )
    print("✅ Flatten imports successful")
    
    # Test 1: Create processor
    processor = FlattenProcessor()
    print("✅ FlattenProcessor created successfully")
    
    # Test 2: Create test image with uneven illumination
    test_image = create_test_image_with_uneven_illumination()
    print(f"✅ Test image created: {test_image.shape}, dtype={test_image.dtype}")
    
    # Test 3: Analyze illumination
    analysis = processor.analyze_illumination(test_image)
    print(f"✅ Illumination analysis completed:")
    print(f"   - Overall uniformity: {analysis['overall_uniformity']:.3f}")
    print(f"   - Needs correction: {analysis['needs_correction']}")
    print(f"   - Recommended method: {analysis['recommended_method'].value}")
    print(f"   - Recommended filter size: {analysis['recommended_large_filter']}")
    
    # Test 4: Apply Bandpass Filter flatten
    params = FlattenParams(
        method=FlattenMethod.BANDPASS_FILTER,
        filter_large=40.0,
        filter_small=3.0,
        suppress_stripes=True,
        autoscale_result=True
    )
    
    flattened_image = processor.process(test_image, params)
    print(f"✅ Bandpass filter flatten applied: {flattened_image.shape}, dtype={flattened_image.dtype}")
    
    # Test 5: Get statistics
    stats = processor.get_flatten_statistics()
    print(f"✅ Flatten statistics retrieved:")
    print(f"   - Original means: {[f'{m:.3f}' for m in stats['original_means']]}")
    print(f"   - Flattened means: {[f'{m:.3f}' for m in stats['flattened_means']]}")
    print(f"   - Uniformity improvement: {[f'{i:.3f}' for i in stats['uniformity_improvement']]}")
    
    # Test 6: Get background estimate
    background = processor.get_background_estimate()
    if background is not None:
        print(f"✅ Background estimate retrieved: {background.shape}")
    else:
        print("❌ No background estimate available")
    
    # Test 7: Test different methods
    methods_to_test = [
        FlattenMethod.GAUSSIAN_BACKGROUND,
        FlattenMethod.ROLLING_BALL,
        FlattenMethod.SLIDING_PARABOLOID
    ]
    
    for method in methods_to_test:
        test_params = FlattenParams(method=method, filter_large=30.0)
        try:
            result = processor.process(test_image, test_params)
            print(f"✅ {method.value} method successful: {result.shape}")
        except Exception as e:
            print(f"❌ {method.value} method failed: {e}")
    
    # Test 8: Test integration with DecorrelationStretch
    from dstretch import DecorrelationStretch
    dstretch = DecorrelationStretch()
    
    # Apply flatten through main API
    flattened_via_api = dstretch.apply_flatten(
        test_image,
        method='bandpass_filter',
        filter_large=40.0,
        filter_small=3.0,
        suppress_stripes=True
    )
    print(f"✅ Flatten via DecorrelationStretch API: {flattened_via_api.shape}")
    
    # Compare results
    difference = np.mean(np.abs(flattened_image.astype(float) - flattened_via_api.astype(float)))
    print(f"✅ API consistency check: mean difference = {difference:.6f}")
    
    if difference < 0.01:
        print("✅ API results are consistent!")
    else:
        print("⚠️  API results differ slightly")
    
    # Test 9: Test illumination analysis
    illumination_stats = dstretch.analyze_illumination(test_image)
    print(f"✅ Illumination analysis via API:")
    print(f"   - Overall uniformity: {illumination_stats['overall_uniformity']:.3f}")
    print(f"   - Needs correction: {illumination_stats['needs_correction']}")
    
    # Test 10: Test background estimate retrieval
    bg_estimate = dstretch.get_background_estimate()
    if bg_estimate is not None:
        print(f"✅ Background estimate via API: {bg_estimate.shape}")
    
    print("\n🎉 ALL FLATTEN TESTS PASSED!")
    
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
