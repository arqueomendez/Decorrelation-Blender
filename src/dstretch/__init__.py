"""
DStretch Python - Decorrelation Stretch for Rock Art Analysis

A Python implementation of the DStretch ImageJ plugin algorithm 
for enhancing archaeological rock art images.
"""

__version__ = "0.1.0"
__author__ = "Your Name"

from .decorrelation import DecorrelationStretch
from .colorspaces import ColorspaceManager, get_available_colorspaces

__all__ = [
    "DecorrelationStretch", 
    "ColorspaceManager",
    "get_available_colorspaces"
]