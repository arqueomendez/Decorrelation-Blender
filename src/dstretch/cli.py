"""
Command line interface for DStretch Python.

Provides a simple CLI that replicates the basic functionality of the DStretch
ImageJ plugin for batch processing and scripting.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from . import DecorrelationStretch, get_available_colorspaces
from .decorrelation import process_image


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='DStretch Python - Decorrelation Stretch for Rock Art Analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic processing with default YDS colorspace
  dstretch input.jpg
  
  # Specify colorspace and intensity
  dstretch input.jpg --colorspace CRGB --scale 25
  
  # Save to specific output file
  dstretch input.jpg --colorspace LRE --output enhanced.jpg
  
  # List available colorspaces
  dstretch --list-colorspaces
        """
    )
    
    # Main arguments
    parser.add_argument(
        'input', 
        nargs='?',
        help='Input image file'
    )
    
    parser.add_argument(
        '-c', '--colorspace',
        default='YDS',
        help='Color space for processing (default: YDS)'
    )
    
    parser.add_argument(
        '-s', '--scale',
        type=float,
        default=15.0,
        help='Enhancement intensity (1-100, default: 15)'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output file path (default: input_colorspace_scale.jpg)'
    )
    
    # Information commands
    parser.add_argument(
        '--list-colorspaces',
        action='store_true',
        help='List all available colorspaces and exit'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='DStretch Python 0.1.0'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    # Handle list colorspaces command
    if args.list_colorspaces:
        print("Available colorspaces:")
        colorspaces = get_available_colorspaces()
        for name, description in colorspaces.items():
            print(f"  {name:<6} - {description}")
        sys.exit(0)
    
    # Validate input file is provided
    if not args.input:
        parser.error("Input image file is required")
    
    # Validate input file exists
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' not found", file=sys.stderr)
        sys.exit(1)
    
    # Validate colorspace
    available_colorspaces = get_available_colorspaces()
    if args.colorspace not in available_colorspaces:
        print(f"Error: Unknown colorspace '{args.colorspace}'", file=sys.stderr)
        print(f"Available colorspaces: {list(available_colorspaces.keys())}", file=sys.stderr)
        sys.exit(1)
    
    # Validate scale
    if not 1.0 <= args.scale <= 100.0:
        print(f"Error: Scale must be between 1 and 100, got {args.scale}", file=sys.stderr)
        sys.exit(1)
    
    # Generate output path if not provided
    if not args.output:
        stem = input_path.stem
        suffix = input_path.suffix if input_path.suffix else '.jpg'
        args.output = f"{stem}_{args.colorspace}_s{int(args.scale)}{suffix}"
    
    output_path = Path(args.output)
    
    # Verbose output
    if args.verbose:
        print(f"Input: {input_path}")
        print(f"Colorspace: {args.colorspace}")
        print(f"Scale: {args.scale}")
        print(f"Output: {output_path}")
    
    try:
        # Process image
        if args.verbose:
            print("Processing image...")
        
        result = process_image(
            str(input_path),
            colorspace=args.colorspace,
            scale=args.scale,
            output_path=str(output_path)
        )
        
        print(f"Successfully processed '{input_path}' -> '{output_path}'")
        
        if args.verbose:
            print(f"Colorspace: {result.colorspace}")
            print(f"Scale: {result.scale}")
            print(f"Output dimensions: {result.processed_image.shape}")
        
    except Exception as e:
        print(f"Error processing image: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()