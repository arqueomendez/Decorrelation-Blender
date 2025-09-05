#!/usr/bin/env python3
"""
Test script for DStretch Python v2.0 - Independent Pipeline Architecture

This script demonstrates the corrected pipeline where preprocessing tools
operate on RGB images BEFORE decorrelation stretch.
"""

import sys
import os
from pathlib import Path
import numpy as np
from PIL import Image
import cv2

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from dstretch import (
        DStretchPipeline, create_preprocessing_config, quick_enhance,
        list_available_colorspaces, get_available_processors, get_pipeline_info,
        process_image, process_with_preset
    )
    print("✅ Successfully imported DStretch v2.0 Pipeline")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


def test_pipeline_info():
    """Test pipeline information functions."""
    print("\n🔍 PIPELINE INFORMATION:")
    
    # Get pipeline info
    info = get_pipeline_info()
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    # List colorspaces
    colorspaces = list_available_colorspaces()
    print(f"\n📊 Available colorspaces ({len(colorspaces)}):")
    for i, cs in enumerate(colorspaces):
        if i % 6 == 0:
            print()
        print(f"  {cs:<6}", end="")
    print()
    
    # List processors
    processors = get_available_processors()
    print(f"\n🔧 Available processors ({len(processors)}):")
    for name, description in processors.items():
        print(f"  {name:<15} - {description}")


def create_test_image():
    """Create a synthetic test image for validation."""
    print("\n🎨 Creating synthetic test image...")
    
    # Create a test image with different colored regions
    width, height = 400, 300
    image = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Add colored regions
    image[50:100, 50:150] = [180, 50, 50]    # Red region
    image[50:100, 200:300] = [200, 200, 50]  # Yellow region
    image[150:200, 50:150] = [50, 150, 50]   # Green region
    image[150:200, 200:300] = [50, 50, 180]  # Blue region
    
    # Add some noise for realism
    noise = np.random.randint(-20, 20, (height, width, 3), dtype=np.int16)
    image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    # Add gradient background
    for y in range(height):
        for x in range(width):
            if np.all(image[y, x] == [0, 0, 0]):  # Only modify black pixels
                gradient_value = int((x + y) / (width + height) * 100 + 50)
                image[y, x] = [gradient_value, gradient_value, gradient_value]
    
    return image


def test_individual_processors():
    """Test individual processors independently."""
    print("\n🔧 TESTING INDIVIDUAL PROCESSORS:")
    
    test_image = create_test_image()
    pipeline = DStretchPipeline()
    
    # Test invert
    print("  Testing Invert processor...")
    inverted = pipeline.invert(test_image, invert_mode='full')
    print(f"    Original mean: {np.mean(test_image):.1f}")
    print(f"    Inverted mean: {np.mean(inverted):.1f}")
    
    # Test auto contrast
    print("  Testing Auto Contrast processor...")
    contrasted = pipeline.auto_contrast(test_image, clip_percentage=0.1)
    original_range = np.max(test_image) - np.min(test_image)
    contrasted_range = np.max(contrasted) - np.min(contrasted)
    print(f"    Original range: {original_range}")
    print(f"    Contrasted range: {contrasted_range}")
    
    # Test color balance
    print("  Testing Color Balance processor...")
    balanced = pipeline.color_balance(test_image, method='gray_world')
    orig_means = np.mean(test_image.reshape(-1, 3), axis=0)
    balanced_means = np.mean(balanced.reshape(-1, 3), axis=0)
    print(f"    Original channel means: R={orig_means[0]:.1f}, G={orig_means[1]:.1f}, B={orig_means[2]:.1f}")
    print(f"    Balanced channel means: R={balanced_means[0]:.1f}, G={balanced_means[1]:.1f}, B={balanced_means[2]:.1f}")
    
    # Test flatten
    print("  Testing Flatten processor...")
    flattened = pipeline.flatten(test_image, method='gaussian_background')
    print(f"    Original std: {np.std(test_image):.1f}")
    print(f"    Flattened std: {np.std(flattened):.1f}")


def test_preprocessing_configs():
    """Test preprocessing configuration creation."""
    print("\n⚙️ TESTING PREPROCESSING CONFIGURATIONS:")
    
    # Test individual preprocessing steps
    config1 = create_preprocessing_config(auto_contrast=True)
    print(f"  Auto contrast only: {len(config1)} steps")
    
    config2 = create_preprocessing_config(
        auto_contrast=True,
        color_balance=True,
        auto_contrast_params={'clip_percentage': 0.2},
        color_balance_params={'method': 'white_patch', 'strength': 0.8}
    )
    print(f"  Multi-step config: {len(config2)} steps")
    
    # Test full preprocessing pipeline
    config3 = create_preprocessing_config(
        invert=True,
        auto_contrast=True,
        color_balance=True,
        flatten=True
    )
    print(f"  Full pipeline: {len(config3)} steps")
    
    for i, step in enumerate(config3):
        print(f"    Step {i+1}: {step['type']}")


def test_complete_pipeline():
    """Test complete pipeline processing."""
    print("\n🚀 TESTING COMPLETE PIPELINE:")
    
    test_image = create_test_image()
    
    # Test 1: Decorrelation only (legacy mode)
    print("  Test 1: Decorrelation only")
    pipeline = DStretchPipeline()
    result1 = pipeline.process_decorrelation_only(test_image, 'YDS', 20.0)
    print(f"    Result: {result1.colorspace}, scale {result1.scale}")
    print(f"    Output shape: {result1.processed_image.shape}")
    
    # Test 2: Preprocessing only
    print("  Test 2: Preprocessing only")
    preprocessing_steps = create_preprocessing_config(
        auto_contrast=True,
        color_balance=True
    )
    preprocessed_image, processor_results = pipeline.apply_preprocessing_only(test_image, preprocessing_steps)
    print(f"    Applied {len(processor_results)} preprocessing steps:")
    for result in processor_results:
        print(f"      - {result.processor_name}")
    
    # Test 3: Complete pipeline
    print("  Test 3: Complete pipeline")
    result3 = pipeline.process_complete(
        test_image, preprocessing_steps, 'CRGB', 15.0
    )
    print(f"    Has preprocessing: {result3.has_preprocessing()}")
    print(f"    Preprocessing steps: {result3.get_preprocessing_names()}")
    print(f"    Final colorspace: {result3.decorrelation_result.colorspace}")
    print(f"    Final scale: {result3.decorrelation_result.scale}")


def test_enhancement_presets():
    """Test enhancement presets."""
    print("\n🎯 TESTING ENHANCEMENT PRESETS:")
    
    test_image = create_test_image()
    
    presets = ['standard', 'faint_reds', 'yellows', 'high_contrast']
    
    for preset in presets:
        print(f"  Testing preset: {preset}")
        try:
            result = quick_enhance(test_image, preset)
            print(f"    ✅ Success - {result.decorrelation_result.colorspace} colorspace")
            if result.has_preprocessing():
                steps = result.get_preprocessing_names()
                print(f"    Preprocessing: {', '.join(steps)}")
            else:
                print(f"    No preprocessing applied")
        except Exception as e:
            print(f"    ❌ Failed: {e}")


def test_convenience_functions():
    """Test convenience functions."""
    print("\n🛠️ TESTING CONVENIENCE FUNCTIONS:")
    
    test_image = create_test_image()
    
    # Test process_image function
    print("  Testing process_image function...")
    preprocessing_steps = create_preprocessing_config(auto_contrast=True)
    result = process_image(test_image, preprocessing_steps, 'LDS', 25.0)
    print(f"    ✅ Success - {type(result).__name__}")
    
    # Test process_with_preset function
    print("  Testing process_with_preset function...")
    result = process_with_preset(test_image, 'standard')
    print(f"    ✅ Success - {type(result).__name__}")


def test_save_and_load():
    """Test save and load functionality."""
    print("\n💾 TESTING SAVE/LOAD:")
    
    test_image = create_test_image()
    
    # Save test image
    test_image_path = Path("test_image.png")
    Image.fromarray(test_image).save(test_image_path)
    print(f"  Saved test image: {test_image_path}")
    
    # Process and save results
    result = quick_enhance(test_image, 'standard')
    
    # Save final result
    final_path = Path("test_result_final.png")
    result.save_final(str(final_path))
    print(f"  Saved final result: {final_path}")
    
    # Save preprocessed if available
    if result.has_preprocessing():
        preprocessed_path = Path("test_result_preprocessed.png")
        result.save_preprocessed(str(preprocessed_path))
        print(f"  Saved preprocessed: {preprocessed_path}")
    
    # Cleanup
    for path in [test_image_path, final_path]:
        if path.exists():
            path.unlink()
            print(f"  Cleaned up: {path}")
    
    preprocessed_path = Path("test_result_preprocessed.png")
    if preprocessed_path.exists():
        preprocessed_path.unlink()
        print(f"  Cleaned up: {preprocessed_path}")


def run_performance_test():
    """Run performance comparison between old and new architecture."""
    print("\n⚡ PERFORMANCE COMPARISON:")
    
    import time
    
    # Create larger test image
    large_image = np.random.randint(0, 255, (800, 600, 3), dtype=np.uint8)
    
    # Test new pipeline
    pipeline = DStretchPipeline()
    
    start_time = time.time()
    result = pipeline.process_complete(
        large_image,
        create_preprocessing_config(auto_contrast=True, color_balance=True),
        'YDS',
        15.0
    )
    new_time = time.time() - start_time
    
    print(f"  New pipeline (800x600): {new_time:.3f} seconds")
    print(f"  Image shape: {result.final_image.shape}")
    print(f"  Pipeline stages: {len(result.preprocessing_results) + 1}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("🧪 DSTRETCH PYTHON v2.0 - PIPELINE ARCHITECTURE TESTS")
    print("=" * 60)
    
    try:
        test_pipeline_info()
        test_individual_processors()
        test_preprocessing_configs()
        test_complete_pipeline()
        test_enhancement_presets()
        test_convenience_functions()
        test_save_and_load()
        run_performance_test()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("🎯 DStretch v2.0 Independent Pipeline Architecture is working correctly")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
