#!/usr/bin/env python3
"""
DStretch Independent Tools - Standalone Script
===============================================

Demonstrates how to use individual DStretch processors without decorrelation.
Each tool works completely independently on RGB images.

Usage Examples:
    python independent_tools.py input.jpg --invert
    python independent_tools.py input.jpg --auto-contrast --output contrast.jpg
    python independent_tools.py input.jpg --color-balance --flatten --output processed.jpg
"""

import argparse
import sys
from pathlib import Path
import cv2
import numpy as np

# Import DStretch independent processors
from src.dstretch.independent_processors import (
    ProcessorFactory, ProcessorType, create_preprocessing_config
)


def main():
    """Main entry point for independent tools."""
    parser = argparse.ArgumentParser(
        description='DStretch Independent Tools - Apply preprocessing without decorrelation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Apply single tools
  python independent_tools.py image.jpg --invert
  python independent_tools.py image.jpg --auto-contrast
  python independent_tools.py image.jpg --color-balance
  python independent_tools.py image.jpg --flatten
  
  # Combine multiple tools
  python independent_tools.py image.jpg --auto-contrast --color-balance
  python independent_tools.py image.jpg --flatten --auto-contrast --output enhanced.jpg
  
  # Tool-specific parameters
  python independent_tools.py image.jpg --auto-contrast --contrast-clip 0.5
  python independent_tools.py image.jpg --color-balance --balance-method white_patch
  python independent_tools.py image.jpg --flatten --flatten-method gaussian
        """
    )
    
    # Main arguments
    parser.add_argument('input', help='Input image file')
    parser.add_argument('-o', '--output', help='Output file (default: auto-generated)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    # Individual tool flags
    parser.add_argument('--invert', action='store_true', help='Apply color inversion')
    
    parser.add_argument('--auto-contrast', action='store_true', help='Apply auto contrast')
    parser.add_argument('--contrast-clip', type=float, default=0.35, 
                       help='Auto contrast clip percentage (default: 0.35)')
    
    parser.add_argument('--color-balance', action='store_true', help='Apply color balance')
    parser.add_argument('--balance-method', choices=['gray_world', 'white_patch', 'manual'],
                       default='gray_world', help='Color balance method (default: gray_world)')
    parser.add_argument('--balance-strength', type=float, default=0.8,
                       help='Color balance strength (default: 0.8)')
    
    parser.add_argument('--flatten', action='store_true', help='Apply flatten illumination')
    parser.add_argument('--flatten-method', 
                       choices=['bandpass', 'gaussian', 'sliding_paraboloid', 'rolling_ball'],
                       default='bandpass', help='Flatten method (default: bandpass)')
    parser.add_argument('--flatten-large', type=int, default=40,
                       help='Large structures to filter (default: 40)')
    parser.add_argument('--flatten-small', type=int, default=3,
                       help='Small structures to preserve (default: 3)')
    
    parser.add_argument('--hue-shift', type=float, help='Hue shift in degrees (-180 to 180)')
    
    # Information
    parser.add_argument('--list-tools', action='store_true', 
                       help='List available tools and exit')
    
    args = parser.parse_args()
    
    # Handle list tools
    if args.list_tools:
        print("Available Independent Tools:")
        for processor_type in ProcessorType:
            print(f"  --{processor_type.value.replace('_', '-'):<15} - {processor_type.value.title()} processor")
        sys.exit(0)
    
    # Validate input
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' not found", file=sys.stderr)
        sys.exit(1)
    
    # Check if any tools are selected
    tools_selected = any([
        args.invert, args.auto_contrast, args.color_balance, 
        args.flatten, args.hue_shift is not None
    ])
    
    if not tools_selected:
        print("Error: No processing tools selected. Use --help for options.", file=sys.stderr)
        sys.exit(1)
    
    # Generate output filename if not provided
    if not args.output:
        stem = input_path.stem
        suffix = input_path.suffix or '.jpg'
        
        # Build suffix based on applied tools
        tool_suffixes = []
        if args.invert:
            tool_suffixes.append('inv')
        if args.auto_contrast:
            tool_suffixes.append('ac')
        if args.color_balance:
            tool_suffixes.append('cb')
        if args.flatten:
            tool_suffixes.append('flat')
        if args.hue_shift is not None:
            tool_suffixes.append(f'hue{int(args.hue_shift)}')
        
        args.output = f"{stem}_{'_'.join(tool_suffixes)}{suffix}"
    
    output_path = Path(args.output)
    
    if args.verbose:
        print(f"DStretch Independent Tools")
        print(f"Input: {input_path}")
        print(f"Output: {output_path}")
        print(f"Tools: {', '.join([t for t in ['invert', 'auto-contrast', 'color-balance', 'flatten', 'hue-shift'] if getattr(args, t.replace('-', '_'), False) or (t == 'hue-shift' and args.hue_shift is not None)])}")
    
    try:
        # Load image
        if args.verbose:
            print("Loading image...")
        
        image = cv2.imread(str(input_path))
        if image is None:
            raise ValueError(f"Could not load image from {input_path}")
        
        # Convert BGR to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        if args.verbose:
            print(f"Image loaded: {image.shape}")
        
        # Apply tools in optimal order
        current_image = image.copy()
        applied_tools = []
        
        # 1. Flatten (correct illumination first)
        if args.flatten:
            if args.verbose:
                print("Applying Flatten...")
            
            processor = ProcessorFactory.create_processor(ProcessorType.FLATTEN)
            result = processor.process(current_image, 
                                     method=args.flatten_method,
                                     large_structures=args.flatten_large,
                                     small_structures=args.flatten_small,
                                     suppress_stripes=True,
                                     auto_scale=True)
            current_image = result.image
            applied_tools.append(f"Flatten ({args.flatten_method})")
            
            if args.verbose and result.statistics:
                improvement = result.statistics.get('overall_improvement', 0)
                print(f"  Improvement: {improvement:.3f}")
        
        # 2. Color Balance (correct color cast)
        if args.color_balance:
            if args.verbose:
                print("Applying Color Balance...")
            
            processor = ProcessorFactory.create_processor(ProcessorType.COLOR_BALANCE)
            result = processor.process(current_image,
                                     method=args.balance_method,
                                     strength=args.balance_strength,
                                     preserve_luminance=True)
            current_image = result.image
            applied_tools.append(f"Color Balance ({args.balance_method})")
            
            if args.verbose and result.statistics:
                improvement = result.statistics.get('overall_improvement', 0)
                print(f"  Improvement: {improvement:.3f}")
        
        # 3. Auto Contrast (optimize dynamic range)
        if args.auto_contrast:
            if args.verbose:
                print("Applying Auto Contrast...")
            
            processor = ProcessorFactory.create_processor(ProcessorType.AUTO_CONTRAST)
            result = processor.process(current_image,
                                     saturated_pixels=args.contrast_clip,
                                     normalize=True)
            current_image = result.image
            applied_tools.append(f"Auto Contrast ({args.contrast_clip}%)")
            
            if args.verbose and result.statistics:
                improvement = result.statistics['overall'].get('contrast_improvement', 1)
                print(f"  Contrast improvement: {improvement:.3f}x")
        
        # 4. Hue Shift (adjust color separation)
        if args.hue_shift is not None:
            if args.verbose:
                print(f"Applying Hue Shift ({args.hue_shift}°)...")
            
            processor = ProcessorFactory.create_processor(ProcessorType.HUE_SHIFT)
            result = processor.process(current_image,
                                     hue_shift=args.hue_shift,
                                     saturation_boost=1.0,
                                     selective=False)
            current_image = result.image
            applied_tools.append(f"Hue Shift ({args.hue_shift}°)")
            
            if args.verbose and result.statistics:
                actual_shift = result.statistics['hue_distribution'].get('hue_shift_applied', 0)
                print(f"  Actual shift applied: {actual_shift:.1f}°")
        
        # 5. Invert (final step if requested)
        if args.invert:
            if args.verbose:
                print("Applying Invert...")
            
            processor = ProcessorFactory.create_processor(ProcessorType.INVERT)
            result = processor.process(current_image)
            current_image = result.image
            applied_tools.append("Invert")
            
            if args.verbose and result.statistics:
                change = result.statistics.get('mean_change', 0)
                print(f"  Mean color change: {change:.1f}")
        
        # Save result
        if args.verbose:
            print("Saving result...")
        
        # Convert RGB back to BGR for OpenCV
        output_image = cv2.cvtColor(current_image, cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(output_path), output_image)
        
        print(f"Successfully processed '{input_path}' -> '{output_path}'")
        
        if args.verbose:
            print(f"Applied tools: {', '.join(applied_tools)}")
            print(f"Final image shape: {current_image.shape}")
        
    except Exception as e:
        print(f"Error processing image: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
