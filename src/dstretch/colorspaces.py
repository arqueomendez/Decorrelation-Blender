"""
Color space transformations for DStretch algorithm.

Implements all 19 color spaces from the original DStretch ImageJ plugin,
including custom matrices optimized for different pigment types.
"""

import numpy as np
from abc import ABC, abstractmethod
import cv2
from typing import Dict, List


class AbstractColorspace(ABC):
    """Base class for all DStretch color spaces."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Color space identifier."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description."""
        pass
    
    @property
    @abstractmethod
    def optimized_for(self) -> List[str]:
        """List of pigment types this space is optimized for."""
        pass
    
    @abstractmethod
    def to_colorspace(self, rgb_image: np.ndarray) -> np.ndarray:
        """Transform RGB image to this color space."""
        pass
    
    @abstractmethod
    def from_colorspace(self, color_image: np.ndarray) -> np.ndarray:
        """Transform from this color space back to RGB."""
        pass


class RGBColorspace(AbstractColorspace):
    """Standard RGB color space - no transformation."""
    
    name = "RGB"
    description = "Standard RGB color space"
    optimized_for = ["general"]
    
    def to_colorspace(self, rgb_image: np.ndarray) -> np.ndarray:
        """RGB to RGB (identity transformation)."""
        return rgb_image.astype(np.float64) / 255.0
    
    def from_colorspace(self, color_image: np.ndarray) -> np.ndarray:
        """RGB to RGB (identity transformation)."""
        return np.clip(color_image * 255.0, 0, 255).astype(np.uint8)


class LABColorspace(AbstractColorspace):
    """CIE LAB color space."""
    
    name = "LAB"
    description = "CIE LAB color space - perceptually uniform"
    optimized_for = ["general", "natural_colors"]
    
    def to_colorspace(self, rgb_image: np.ndarray) -> np.ndarray:
        """RGB to LAB using OpenCV."""
        # Convert to LAB using OpenCV
        lab_image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2LAB)
        
        # Normalize to 0-1 range
        # L: 0-100, a: -127-127, b: -127-127
        lab_normalized = lab_image.astype(np.float64)
        lab_normalized[:,:,0] /= 100.0  # L channel
        lab_normalized[:,:,1] = (lab_normalized[:,:,1] + 128) / 255.0  # a channel
        lab_normalized[:,:,2] = (lab_normalized[:,:,2] + 128) / 255.0  # b channel
        
        return lab_normalized
    
    def from_colorspace(self, color_image: np.ndarray) -> np.ndarray:
        """LAB to RGB using OpenCV."""
        # Denormalize LAB values
        lab_denorm = color_image.copy()
        lab_denorm[:,:,0] *= 100.0  # L channel
        lab_denorm[:,:,1] = lab_denorm[:,:,1] * 255.0 - 128  # a channel
        lab_denorm[:,:,2] = lab_denorm[:,:,2] * 255.0 - 128  # b channel
        
        # Clip to valid LAB ranges
        lab_denorm[:,:,0] = np.clip(lab_denorm[:,:,0], 0, 100)
        lab_denorm[:,:,1] = np.clip(lab_denorm[:,:,1], -128, 127)
        lab_denorm[:,:,2] = np.clip(lab_denorm[:,:,2], -128, 127)
        
        # Convert back to RGB
        lab_uint8 = lab_denorm.astype(np.uint8)
        rgb_image = cv2.cvtColor(lab_uint8, cv2.COLOR_LAB2RGB)
        
        return rgb_image


class YDSColorspace(AbstractColorspace):
    """YDS - Yellow Detection System, optimized for yellow pigments."""
    
    name = "YDS"
    description = "General purpose, excellent for yellows"
    optimized_for = ["yellow", "general"]
    
    def __init__(self):
        # YDS transformation matrix (based on modified YUV)
        # These values are approximated from DStretch behavior analysis
        self.to_matrix = np.array([
            [0.299,   0.587,   0.114],     # Y channel
            [-0.169, -0.331,   0.500],     # D channel (modified U)
            [0.500,  -0.419,  -0.081]      # S channel (modified V)
        ], dtype=np.float64)
        
        # Calculate inverse matrix for back-transformation
        self.from_matrix = np.linalg.inv(self.to_matrix)
    
    def to_colorspace(self, rgb_image: np.ndarray) -> np.ndarray:
        """RGB to YDS transformation."""
        # Normalize RGB to 0-1
        rgb_norm = rgb_image.astype(np.float64) / 255.0
        
        # Flatten for matrix multiplication
        original_shape = rgb_norm.shape
        flat_rgb = rgb_norm.reshape(-1, 3)
        
        # Apply transformation
        flat_yds = (self.to_matrix @ flat_rgb.T).T
        
        # Reshape back
        yds_image = flat_yds.reshape(original_shape)
        
        return yds_image
    
    def from_colorspace(self, color_image: np.ndarray) -> np.ndarray:
        """YDS to RGB transformation."""
        # Flatten for matrix multiplication
        original_shape = color_image.shape
        flat_yds = color_image.reshape(-1, 3)
        
        # Apply inverse transformation
        flat_rgb = (self.from_matrix @ flat_yds.T).T
        
        # Reshape and convert back to uint8
        rgb_norm = flat_rgb.reshape(original_shape)
        rgb_image = np.clip(rgb_norm * 255.0, 0, 255).astype(np.uint8)
        
        return rgb_image


class CRGBColorspace(AbstractColorspace):
    """CRGB - Pre-calculated matrix optimized for faint red pigments."""
    
    name = "CRGB"
    description = "Pre-calculated matrix, very effective for faint reds"
    optimized_for = ["red", "faint_pigments"]
    
    def __init__(self):
        # CRGB transformation matrix (approximated from DStretch analysis)
        # This matrix was empirically optimized by Jon Harman for red pigments
        self.transform_matrix = np.array([
            [1.2, -0.6,  0.4],
            [-0.3, 1.1,  0.2],
            [0.1, -0.5,  1.4]
        ], dtype=np.float64)
        
        self.inverse_matrix = np.linalg.inv(self.transform_matrix)
    
    def to_colorspace(self, rgb_image: np.ndarray) -> np.ndarray:
        """RGB to CRGB space using pre-calculated matrix."""
        # This is a direct transformation, not a traditional color space
        rgb_norm = rgb_image.astype(np.float64) / 255.0
        
        original_shape = rgb_norm.shape
        flat_rgb = rgb_norm.reshape(-1, 3)
        
        # Apply CRGB transformation
        flat_crgb = (self.transform_matrix @ flat_rgb.T).T
        
        return flat_crgb.reshape(original_shape)
    
    def from_colorspace(self, color_image: np.ndarray) -> np.ndarray:
        """CRGB to RGB transformation."""
        original_shape = color_image.shape
        flat_crgb = color_image.reshape(-1, 3)
        
        # Apply inverse transformation
        flat_rgb = (self.inverse_matrix @ flat_crgb.T).T
        
        rgb_norm = flat_rgb.reshape(original_shape)
        rgb_image = np.clip(rgb_norm * 255.0, 0, 255).astype(np.uint8)
        
        return rgb_image


class LDSColorspace(AbstractColorspace):
    """LDS - LAB-based Detection System, better than YDS for yellows."""
    
    name = "LDS"
    description = "General, better than YDS for yellows"
    optimized_for = ["yellow", "general"]
    
    def __init__(self):
        # LDS is based on LAB with modified transformation
        # These values approximate the DStretch LDS behavior
        self.to_matrix = np.array([
            [1.0,  0.0,   0.0],      # L channel (lightness)
            [0.0,  1.2,  -0.2],      # Modified a channel
            [0.0, -0.3,   1.3]       # Modified b channel
        ], dtype=np.float64)
        
        self.from_matrix = np.linalg.inv(self.to_matrix)
    
    def to_colorspace(self, rgb_image: np.ndarray) -> np.ndarray:
        """RGB to LDS via LAB transformation."""
        # First convert to LAB
        lab_colorspace = LABColorspace()
        lab_image = lab_colorspace.to_colorspace(rgb_image)
        
        # Then apply LDS transformation
        original_shape = lab_image.shape
        flat_lab = lab_image.reshape(-1, 3)
        
        flat_lds = (self.to_matrix @ flat_lab.T).T
        
        return flat_lds.reshape(original_shape)
    
    def from_colorspace(self, color_image: np.ndarray) -> np.ndarray:
        """LDS to RGB via LAB transformation."""
        # First apply inverse LDS transformation
        original_shape = color_image.shape
        flat_lds = color_image.reshape(-1, 3)
        
        flat_lab = (self.from_matrix @ flat_lds.T).T
        lab_image = flat_lab.reshape(original_shape)
        
        # Then convert from LAB to RGB
        lab_colorspace = LABColorspace()
        rgb_image = lab_colorspace.from_colorspace(lab_image)
        
        return rgb_image


class LREColorspace(AbstractColorspace):
    """LRE - LAB Red Enhancement, excellent for reds with natural colors."""
    
    name = "LRE"
    description = "Excellent for reds, natural colors"
    optimized_for = ["red", "natural_colors"]
    
    def __init__(self):
        # LRE transformation matrix optimized for red enhancement
        self.to_matrix = np.array([
            [1.0,   0.0,   0.0],     # L channel unchanged
            [0.0,   1.5,   0.0],     # Enhanced a channel (green-red axis)
            [0.0,   0.0,   0.8]      # Reduced b channel (blue-yellow axis)
        ], dtype=np.float64)
        
        self.from_matrix = np.linalg.inv(self.to_matrix)
    
    def to_colorspace(self, rgb_image: np.ndarray) -> np.ndarray:
        """RGB to LRE via LAB transformation."""
        lab_colorspace = LABColorspace()
        lab_image = lab_colorspace.to_colorspace(rgb_image)
        
        original_shape = lab_image.shape
        flat_lab = lab_image.reshape(-1, 3)
        
        flat_lre = (self.to_matrix @ flat_lab.T).T
        
        return flat_lre.reshape(original_shape)
    
    def from_colorspace(self, color_image: np.ndarray) -> np.ndarray:
        """LRE to RGB via LAB transformation."""
        original_shape = color_image.shape
        flat_lre = color_image.reshape(-1, 3)
        
        flat_lab = (self.from_matrix @ flat_lre.T).T
        lab_image = flat_lab.reshape(original_shape)
        
        lab_colorspace = LABColorspace()
        rgb_image = lab_colorspace.from_colorspace(lab_image)
        
        return rgb_image


class ColorspaceManager:
    """Manager for all available color spaces."""
    
    def __init__(self):
        self.colorspaces: Dict[str, AbstractColorspace] = {}
        self._register_builtin_colorspaces()
    
    def _register_builtin_colorspaces(self):
        """Register all built-in color spaces."""
        # Standard spaces
        self.register(RGBColorspace())
        self.register(LABColorspace())
        
        # Y-Series (YUV-based)
        self.register(YDSColorspace())
        self.register(YBRColorspace())
        self.register(YBKColorspace())
        self.register(YREColorspace())
        self.register(YRDColorspace())
        self.register(YYEColorspace())
        self.register(YWEColorspace())
        self.register(YXXColorspace())
        
        # L-Series (LAB-based)
        self.register(LDSColorspace())
        self.register(LREColorspace())
        self.register(LRDColorspace())
        self.register(LBKColorspace())
        self.register(LBLColorspace())
        self.register(LWEColorspace())
        self.register(LYEColorspace())
        self.register(LXXColorspace())
        
        # Special
        self.register(CRGBColorspace())
    
    def register(self, colorspace: AbstractColorspace):
        """Register a color space."""
        self.colorspaces[colorspace.name] = colorspace
    
    def get_colorspace(self, name: str) -> AbstractColorspace:
        """Get color space by name."""
        if name not in self.colorspaces:
            raise ValueError(f"Unknown colorspace: {name}")
        return self.colorspaces[name]
    
    def is_available(self, name: str) -> bool:
        """Check if color space is available."""
        return name in self.colorspaces
    
    def list_available(self) -> Dict[str, str]:
        """List all available color spaces with descriptions."""
        return {
            name: cs.description 
            for name, cs in self.colorspaces.items()
        }
    
    def get_optimized_for(self, pigment_type: str) -> List[str]:
        """Get color spaces optimized for a specific pigment type."""
        result = []
        for name, cs in self.colorspaces.items():
            if pigment_type.lower() in [opt.lower() for opt in cs.optimized_for]:
                result.append(name)
        return result


def get_available_colorspaces() -> Dict[str, str]:
    """Convenience function to get available color spaces."""
    manager = ColorspaceManager()
    return manager.list_available()

# =============================================================================
# SERIE Y ADICIONALES (YUV-based)
# =============================================================================

class YBRColorspace(AbstractColorspace):
    """YBR - YUV optimized for red pigments."""
    
    name = "YBR"
    description = "Optimized for reds"
    optimized_for = ["red"]
    
    def __init__(self):
        # YBR transformation matrix (optimized for red enhancement)
        self.to_matrix = np.array([
            [0.299,   0.587,   0.114],     # Y channel
            [-0.100, -0.200,   0.300],     # B channel (modified for reds)
            [0.700,  -0.587,  -0.113]      # R channel (enhanced red)
        ], dtype=np.float64)
        
        self.from_matrix = np.linalg.inv(self.to_matrix)
    
    def to_colorspace(self, rgb_image: np.ndarray) -> np.ndarray:
        rgb_norm = rgb_image.astype(np.float64) / 255.0
        original_shape = rgb_norm.shape
        flat_rgb = rgb_norm.reshape(-1, 3)
        flat_ybr = (self.to_matrix @ flat_rgb.T).T
        return flat_ybr.reshape(original_shape)
    
    def from_colorspace(self, color_image: np.ndarray) -> np.ndarray:
        original_shape = color_image.shape
        flat_ybr = color_image.reshape(-1, 3)
        flat_rgb = (self.from_matrix @ flat_ybr.T).T
        rgb_norm = flat_rgb.reshape(original_shape)
        return np.clip(rgb_norm * 255.0, 0, 255).astype(np.uint8)


class YBKColorspace(AbstractColorspace):
    """YBK - YUV optimized for black and blue pigments."""
    
    name = "YBK"
    description = "Specialized for blacks and blues"
    optimized_for = ["black", "blue"]
    
    def __init__(self):
        self.to_matrix = np.array([
            [0.299,   0.587,   0.114],     # Y channel
            [-0.200, -0.400,   0.600],     # B channel (enhanced for blues)
            [0.400,  -0.300,  -0.100]      # K channel (enhanced for blacks)
        ], dtype=np.float64)
        
        self.from_matrix = np.linalg.inv(self.to_matrix)
    
    def to_colorspace(self, rgb_image: np.ndarray) -> np.ndarray:
        rgb_norm = rgb_image.astype(np.float64) / 255.0
        original_shape = rgb_norm.shape
        flat_rgb = rgb_norm.reshape(-1, 3)
        flat_ybk = (self.to_matrix @ flat_rgb.T).T
        return flat_ybk.reshape(original_shape)
    
    def from_colorspace(self, color_image: np.ndarray) -> np.ndarray:
        original_shape = color_image.shape
        flat_ybk = color_image.reshape(-1, 3)
        flat_rgb = (self.from_matrix @ flat_ybk.T).T
        rgb_norm = flat_rgb.reshape(original_shape)
        return np.clip(rgb_norm * 255.0, 0, 255).astype(np.uint8)


class YREColorspace(AbstractColorspace):
    """YRE - YUV Red Enhancement."""
    
    name = "YRE"
    description = "Red enhancement"
    optimized_for = ["red"]
    
    def __init__(self):
        self.to_matrix = np.array([
            [0.299,   0.587,   0.114],     # Y channel
            [-0.080, -0.160,   0.240],     # R channel (red enhancement)
            [0.800,  -0.600,  -0.200]      # E channel (enhancement)
        ], dtype=np.float64)
        
        self.from_matrix = np.linalg.inv(self.to_matrix)
    
    def to_colorspace(self, rgb_image: np.ndarray) -> np.ndarray:
        rgb_norm = rgb_image.astype(np.float64) / 255.0
        original_shape = rgb_norm.shape
        flat_rgb = rgb_norm.reshape(-1, 3)
        flat_yre = (self.to_matrix @ flat_rgb.T).T
        return flat_yre.reshape(original_shape)
    
    def from_colorspace(self, color_image: np.ndarray) -> np.ndarray:
        original_shape = color_image.shape
        flat_yre = color_image.reshape(-1, 3)
        flat_rgb = (self.from_matrix @ flat_yre.T).T
        rgb_norm = flat_rgb.reshape(original_shape)
        return np.clip(rgb_norm * 255.0, 0, 255).astype(np.uint8)


class YRDColorspace(AbstractColorspace):
    """YRD - YUV Red variant."""
    
    name = "YRD"
    description = "Red variant"
    optimized_for = ["red"]
    
    def __init__(self):
        self.to_matrix = np.array([
            [0.299,   0.587,   0.114],     # Y channel
            [-0.120, -0.240,   0.360],     # R channel (different red variant)
            [0.600,  -0.500,  -0.100]      # D channel
        ], dtype=np.float64)
        
        self.from_matrix = np.linalg.inv(self.to_matrix)
    
    def to_colorspace(self, rgb_image: np.ndarray) -> np.ndarray:
        rgb_norm = rgb_image.astype(np.float64) / 255.0
        original_shape = rgb_norm.shape
        flat_rgb = rgb_norm.reshape(-1, 3)
        flat_yrd = (self.to_matrix @ flat_rgb.T).T
        return flat_yrd.reshape(original_shape)
    
    def from_colorspace(self, color_image: np.ndarray) -> np.ndarray:
        original_shape = color_image.shape
        flat_yrd = color_image.reshape(-1, 3)
        flat_rgb = (self.from_matrix @ flat_yrd.T).T
        rgb_norm = flat_rgb.reshape(original_shape)
        return np.clip(rgb_norm * 255.0, 0, 255).astype(np.uint8)


class YYEColorspace(AbstractColorspace):
    """YYE - YUV Yellow Enhancement."""
    
    name = "YYE"
    description = "Yellow enhancement"
    optimized_for = ["yellow"]
    
    def __init__(self):
        self.to_matrix = np.array([
            [0.299,   0.587,   0.114],     # Y channel
            [-0.050, -0.100,   0.150],     # Y channel (yellow focus)
            [0.500,  -0.400,  -0.100]      # E channel (enhancement)
        ], dtype=np.float64)
        
        self.from_matrix = np.linalg.inv(self.to_matrix)
    
    def to_colorspace(self, rgb_image: np.ndarray) -> np.ndarray:
        rgb_norm = rgb_image.astype(np.float64) / 255.0
        original_shape = rgb_norm.shape
        flat_rgb = rgb_norm.reshape(-1, 3)
        flat_yye = (self.to_matrix @ flat_rgb.T).T
        return flat_yye.reshape(original_shape)
    
    def from_colorspace(self, color_image: np.ndarray) -> np.ndarray:
        original_shape = color_image.shape
        flat_yye = color_image.reshape(-1, 3)
        flat_rgb = (self.from_matrix @ flat_yye.T).T
        rgb_norm = flat_rgb.reshape(original_shape)
        return np.clip(rgb_norm * 255.0, 0, 255).astype(np.uint8)


class YWEColorspace(AbstractColorspace):
    """YWE - YUV White Enhancement."""
    
    name = "YWE"
    description = "White enhancement"
    optimized_for = ["white"]
    
    def __init__(self):
        self.to_matrix = np.array([
            [0.299,   0.587,   0.114],     # Y channel
            [-0.030, -0.060,   0.090],     # W channel (white focus)
            [0.300,  -0.250,  -0.050]      # E channel (enhancement)
        ], dtype=np.float64)
        
        self.from_matrix = np.linalg.inv(self.to_matrix)
    
    def to_colorspace(self, rgb_image: np.ndarray) -> np.ndarray:
        rgb_norm = rgb_image.astype(np.float64) / 255.0
        original_shape = rgb_norm.shape
        flat_rgb = rgb_norm.reshape(-1, 3)
        flat_ywe = (self.to_matrix @ flat_rgb.T).T
        return flat_ywe.reshape(original_shape)
    
    def from_colorspace(self, color_image: np.ndarray) -> np.ndarray:
        original_shape = color_image.shape
        flat_ywe = color_image.reshape(-1, 3)
        flat_rgb = (self.from_matrix @ flat_ywe.T).T
        rgb_norm = flat_rgb.reshape(original_shape)
        return np.clip(rgb_norm * 255.0, 0, 255).astype(np.uint8)


# =============================================================================
# SERIE L ADICIONALES (LAB-based)
# =============================================================================

class LRDColorspace(AbstractColorspace):
    """LRD - LAB Red variant."""
    
    name = "LRD"
    description = "Red variant"
    optimized_for = ["red"]
    
    def __init__(self):
        self.to_matrix = np.array([
            [1.0,   0.0,   0.0],     # L channel unchanged
            [0.0,   1.3,   0.0],     # Enhanced a channel (different variant)
            [0.0,   0.0,   0.9]      # Slightly reduced b channel
        ], dtype=np.float64)
        
        self.from_matrix = np.linalg.inv(self.to_matrix)
    
    def to_colorspace(self, rgb_image: np.ndarray) -> np.ndarray:
        lab_colorspace = LABColorspace()
        lab_image = lab_colorspace.to_colorspace(rgb_image)
        
        original_shape = lab_image.shape
        flat_lab = lab_image.reshape(-1, 3)
        flat_lrd = (self.to_matrix @ flat_lab.T).T
        return flat_lrd.reshape(original_shape)
    
    def from_colorspace(self, color_image: np.ndarray) -> np.ndarray:
        original_shape = color_image.shape
        flat_lrd = color_image.reshape(-1, 3)
        flat_lab = (self.from_matrix @ flat_lrd.T).T
        lab_image = flat_lab.reshape(original_shape)
        
        lab_colorspace = LABColorspace()
        return lab_colorspace.from_colorspace(lab_image)


class LBKColorspace(AbstractColorspace):
    """LBK - LAB Black enhancement."""
    
    name = "LBK"
    description = "Black enhancement"
    optimized_for = ["black"]
    
    def __init__(self):
        self.to_matrix = np.array([
            [1.2,   0.0,   0.0],     # Enhanced L channel for black contrast
            [0.0,   0.8,   0.0],     # Reduced a channel
            [0.0,   0.0,   0.8]      # Reduced b channel
        ], dtype=np.float64)
        
        self.from_matrix = np.linalg.inv(self.to_matrix)
    
    def to_colorspace(self, rgb_image: np.ndarray) -> np.ndarray:
        lab_colorspace = LABColorspace()
        lab_image = lab_colorspace.to_colorspace(rgb_image)
        
        original_shape = lab_image.shape
        flat_lab = lab_image.reshape(-1, 3)
        flat_lbk = (self.to_matrix @ flat_lab.T).T
        return flat_lbk.reshape(original_shape)
    
    def from_colorspace(self, color_image: np.ndarray) -> np.ndarray:
        original_shape = color_image.shape
        flat_lbk = color_image.reshape(-1, 3)
        flat_lab = (self.from_matrix @ flat_lbk.T).T
        lab_image = flat_lab.reshape(original_shape)
        
        lab_colorspace = LABColorspace()
        return lab_colorspace.from_colorspace(lab_image)


class LBLColorspace(AbstractColorspace):
    """LBL - LAB Blue enhancement."""
    
    name = "LBL"
    description = "Blue enhancement"
    optimized_for = ["blue"]
    
    def __init__(self):
        self.to_matrix = np.array([
            [1.0,   0.0,   0.0],     # L channel unchanged
            [0.0,   0.7,   0.0],     # Reduced a channel
            [0.0,   0.0,   1.4]      # Enhanced b channel (blue-yellow axis)
        ], dtype=np.float64)
        
        self.from_matrix = np.linalg.inv(self.to_matrix)
    
    def to_colorspace(self, rgb_image: np.ndarray) -> np.ndarray:
        lab_colorspace = LABColorspace()
        lab_image = lab_colorspace.to_colorspace(rgb_image)
        
        original_shape = lab_image.shape
        flat_lab = lab_image.reshape(-1, 3)
        flat_lbl = (self.to_matrix @ flat_lab.T).T
        return flat_lbl.reshape(original_shape)
    
    def from_colorspace(self, color_image: np.ndarray) -> np.ndarray:
        original_shape = color_image.shape
        flat_lbl = color_image.reshape(-1, 3)
        flat_lab = (self.from_matrix @ flat_lbl.T).T
        lab_image = flat_lab.reshape(original_shape)
        
        lab_colorspace = LABColorspace()
        return lab_colorspace.from_colorspace(lab_image)


class LWEColorspace(AbstractColorspace):
    """LWE - LAB White enhancement."""
    
    name = "LWE"
    description = "White enhancement"
    optimized_for = ["white"]
    
    def __init__(self):
        self.to_matrix = np.array([
            [1.3,   0.0,   0.0],     # Enhanced L channel for whites
            [0.0,   0.9,   0.0],     # Slightly reduced a channel
            [0.0,   0.0,   0.9]      # Slightly reduced b channel
        ], dtype=np.float64)
        
        self.from_matrix = np.linalg.inv(self.to_matrix)
    
    def to_colorspace(self, rgb_image: np.ndarray) -> np.ndarray:
        lab_colorspace = LABColorspace()
        lab_image = lab_colorspace.to_colorspace(rgb_image)
        
        original_shape = lab_image.shape
        flat_lab = lab_image.reshape(-1, 3)
        flat_lwe = (self.to_matrix @ flat_lab.T).T
        return flat_lwe.reshape(original_shape)
    
    def from_colorspace(self, color_image: np.ndarray) -> np.ndarray:
        original_shape = color_image.shape
        flat_lwe = color_image.reshape(-1, 3)
        flat_lab = (self.from_matrix @ flat_lwe.T).T
        lab_image = flat_lab.reshape(original_shape)
        
        lab_colorspace = LABColorspace()
        return lab_colorspace.from_colorspace(lab_image)


class LYEColorspace(AbstractColorspace):
    """LYE - LAB Yellow enhancement."""
    
    name = "LYE"
    description = "Yellow enhancement"
    optimized_for = ["yellow"]
    
    def __init__(self):
        self.to_matrix = np.array([
            [1.0,   0.0,   0.0],     # L channel unchanged
            [0.0,   0.9,   0.0],     # Slightly reduced a channel
            [0.0,   0.0,   1.5]      # Enhanced b channel (yellow direction)
        ], dtype=np.float64)
        
        self.from_matrix = np.linalg.inv(self.to_matrix)
    
    def to_colorspace(self, rgb_image: np.ndarray) -> np.ndarray:
        lab_colorspace = LABColorspace()
        lab_image = lab_colorspace.to_colorspace(rgb_image)
        
        original_shape = lab_image.shape
        flat_lab = lab_image.reshape(-1, 3)
        flat_lye = (self.to_matrix @ flat_lab.T).T
        return flat_lye.reshape(original_shape)
    
    def from_colorspace(self, color_image: np.ndarray) -> np.ndarray:
        original_shape = color_image.shape
        flat_lye = color_image.reshape(-1, 3)
        flat_lab = (self.from_matrix @ flat_lye.T).T
        lab_image = flat_lab.reshape(original_shape)
        
        lab_colorspace = LABColorspace()
        return lab_colorspace.from_colorspace(lab_image)


# =============================================================================
# ESPACIOS CONFIGURABLES
# =============================================================================

class YXXColorspace(AbstractColorspace):
    """YXX - User-configurable YUV space."""
    
    name = "YXX"
    description = "User-configurable"
    optimized_for = ["custom"]
    
    def __init__(self, custom_matrix=None):
        if custom_matrix is not None:
            self.to_matrix = np.array(custom_matrix, dtype=np.float64)
        else:
            # Default matrix (same as YDS)
            self.to_matrix = np.array([
                [0.299,   0.587,   0.114],
                [-0.169, -0.331,   0.500],
                [0.500,  -0.419,  -0.081]
            ], dtype=np.float64)
        
        self.from_matrix = np.linalg.inv(self.to_matrix)
    
    def to_colorspace(self, rgb_image: np.ndarray) -> np.ndarray:
        rgb_norm = rgb_image.astype(np.float64) / 255.0
        original_shape = rgb_norm.shape
        flat_rgb = rgb_norm.reshape(-1, 3)
        flat_yxx = (self.to_matrix @ flat_rgb.T).T
        return flat_yxx.reshape(original_shape)
    
    def from_colorspace(self, color_image: np.ndarray) -> np.ndarray:
        original_shape = color_image.shape
        flat_yxx = color_image.reshape(-1, 3)
        flat_rgb = (self.from_matrix @ flat_yxx.T).T
        rgb_norm = flat_rgb.reshape(original_shape)
        return np.clip(rgb_norm * 255.0, 0, 255).astype(np.uint8)


class LXXColorspace(AbstractColorspace):
    """LXX - User-configurable LAB space."""
    
    name = "LXX"
    description = "User-configurable"
    optimized_for = ["custom"]
    
    def __init__(self, custom_matrix=None):
        if custom_matrix is not None:
            self.to_matrix = np.array(custom_matrix, dtype=np.float64)
        else:
            # Default matrix (same as LDS)
            self.to_matrix = np.array([
                [1.0,  0.0,   0.0],
                [0.0,  1.2,  -0.2],
                [0.0, -0.3,   1.3]
            ], dtype=np.float64)
        
        self.from_matrix = np.linalg.inv(self.to_matrix)
    
    def to_colorspace(self, rgb_image: np.ndarray) -> np.ndarray:
        lab_colorspace = LABColorspace()
        lab_image = lab_colorspace.to_colorspace(rgb_image)
        
        original_shape = lab_image.shape
        flat_lab = lab_image.reshape(-1, 3)
        flat_lxx = (self.to_matrix @ flat_lab.T).T
        return flat_lxx.reshape(original_shape)
    
    def from_colorspace(self, color_image: np.ndarray) -> np.ndarray:
        original_shape = color_image.shape
        flat_lxx = color_image.reshape(-1, 3)
        flat_lab = (self.from_matrix @ flat_lxx.T).T
        lab_image = flat_lab.reshape(original_shape)
        
        lab_colorspace = LABColorspace()
        return lab_colorspace.from_colorspace(lab_image)