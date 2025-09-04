"""
DStretch Python - Decorrelation Stretch for Rock Art Analysis

A Python implementation of the DStretch ImageJ plugin algorithm 
for enhancing archaeological rock art images.
"""

__version__ = "0.1.0"
__author__ = "Your Name"

from .decorrelation import DecorrelationStretch, ProcessingResult
from .colorspaces import COLORSPACES
from .invert_processor import InvertProcessor
from .auto_contrast_processor import AutoContrastProcessor
from .pixel_inspector import PixelInspectorPanel, ColorSpaceConverter, PixelAnalyzer
from .zoom_pan_controller import ZoomPanController, ZoomToolbar
from .gui_infrastructure import (
    ErrorManager, AdvancedStatusBar, TooltipManager, 
    PerformanceManager, ThreadManager, GUIInfrastructure
)

# Opcional: una función de ayuda para listar los espacios de color disponibles.
def list_available_colorspaces():
    """Returns a list of available colorspace names."""
    return list(COLORSPACES.keys())
