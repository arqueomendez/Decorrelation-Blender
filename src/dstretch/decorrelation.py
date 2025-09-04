"""
Core decorrelation stretch algorithm implementation - FINAL CORRECTED VERSION 4.0

This version incorporates the final correction: using the `scale_adjust_factor`
from the colorspace definitions to replicate the original Java plugin's behavior
of varying enhancement intensity across different colorspace families.
"""
import numpy as np
from scipy.linalg import eigh
from typing import Tuple, Optional
import cv2
from .colorspaces import COLORSPACES, AbstractColorspace, BuiltinMatrixColorspace
from .invert_processor import InvertProcessor
from .auto_contrast_processor import AutoContrastProcessor

class ProcessingResult:
    # (Sin cambios)
    def __init__(self, processed_image, original_image, colorspace, scale, final_matrix, color_mean):
        self.processed_image, self.original_image, self.colorspace, self.scale, self.final_matrix, self.color_mean = \
            processed_image, original_image, colorspace, scale, final_matrix, color_mean
    def save(self, filepath: str):
        cv2.imwrite(filepath, cv2.cvtColor(self.processed_image, cv2.COLOR_RGB2BGR))

class DecorrelationStretch:
    def __init__(self):
        self.colorspaces = COLORSPACES
        self._last_original = None
        self._last_processed = None
        self.invert_processor = InvertProcessor()
        self.auto_contrast_processor = AutoContrastProcessor()
    
    def process(self, image: np.ndarray, colorspace: str = "YDS", scale: float = 15.0, 
                selection_mask: Optional[np.ndarray] = None) -> ProcessingResult:
        
        self._validate_inputs(image, colorspace, scale)
        self._last_original = image.copy()
        
        colorspace_obj = self.colorspaces[colorspace]
        
        if isinstance(colorspace_obj, BuiltinMatrixColorspace):
            # --- RUTA 2: MATRIZ PREDEFINIDA (PROBADA Y FUNCIONAL) ---
            base_cs_name = colorspace_obj.base_colorspace_name
            base_cs_obj = self.colorspaces[base_cs_name]
            base_image = base_cs_obj.to_colorspace(image)
            pixel_data = self._get_analysis_data(base_image, selection_mask)
            color_mean = np.mean(pixel_data, axis=0)
            transform_matrix = colorspace_obj.matrix * (scale / 10.0)
            processed_base = self._apply_transformation(base_image, transform_matrix, color_mean)
            processed_rgb = base_cs_obj.from_colorspace(processed_base)
            final_matrix_for_result = transform_matrix
        else:
            # --- RUTA 1: ANÁLISIS ESTADÍSTICO (CON AJUSTE DE ESCALA) ---
            
            # ** CAMBIO CLAVE: Aplicar el factor de ajuste de escala **
            adjusted_scale = scale * colorspace_obj.scale_adjust_factor
            
            transformed_image = colorspace_obj.to_colorspace(image)
            pixel_data = self._get_analysis_data(transformed_image, selection_mask)
            color_mean, covariance_matrix = self._calculate_statistics(pixel_data)
            eigenvalues, eigenvectors = self._eigendecomposition(covariance_matrix)
            
            # Usar la escala ajustada para construir la matriz de estiramiento
            stretch_matrix = self._build_stretch_matrix(eigenvalues, adjusted_scale)
            
            transform_matrix = eigenvectors @ stretch_matrix @ eigenvectors.T
            
            processed_transformed = self._apply_transformation(
                transformed_image, transform_matrix, color_mean
            )
            processed_rgb = colorspace_obj.from_colorspace(processed_transformed)
            final_matrix_for_result = transform_matrix
            
        self._last_processed = processed_rgb
        
        return ProcessingResult(
            processed_image=processed_rgb, original_image=image, colorspace=colorspace,
            scale=scale, final_matrix=final_matrix_for_result, color_mean=color_mean
        )

    # (El resto de los métodos de la clase permanecen sin cambios)
    def _validate_inputs(self, image: np.ndarray, colorspace: str, scale: float):
        if not isinstance(image, np.ndarray) or image.ndim != 3 or image.shape[2] != 3 or image.dtype != np.uint8:
            raise ValueError("Image must be a numpy array of shape (H, W, 3) and dtype uint8")
        if colorspace not in self.colorspaces:
            raise ValueError(f"Unknown colorspace '{colorspace}'. Available: {list(self.colorspaces.keys())}")
        if not 1.0 <= scale <= 100.0:
            raise ValueError("Scale must be between 1.0 and 100.0")
    def _get_analysis_data(self, transformed_image: np.ndarray, selection_mask: Optional[np.ndarray]) -> np.ndarray:
        if selection_mask is not None:
            if selection_mask.shape[:2] != transformed_image.shape[:2] or selection_mask.dtype != bool:
                raise ValueError("Selection mask must match image dimensions and be boolean")
            return transformed_image[selection_mask]
        else:
            return transformed_image.reshape(-1, 3)
    def _calculate_statistics(self, pixel_data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        data = pixel_data.astype(np.float64)
        color_mean = np.mean(data, axis=0)
        covariance = np.cov(data.T)
        return color_mean, covariance
    def _eigendecomposition(self, covariance_matrix: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        eigenvalues, eigenvectors = eigh(covariance_matrix)
        idx = np.argsort(eigenvalues)[::-1]
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]
        return eigenvalues, eigenvectors
    def _build_stretch_matrix(self, eigenvalues: np.ndarray, scale: float) -> np.ndarray:
        eigenvalues[eigenvalues < 1e-10] = 1e-10
        stretch_factors = scale / np.sqrt(eigenvalues)
        return np.diag(stretch_factors)
    def _apply_transformation(self, transformed_image: np.ndarray, transform_matrix: np.ndarray, color_mean: np.ndarray) -> np.ndarray:
        original_shape = transformed_image.shape
        flat_image = transformed_image.reshape(-1, 3).astype(np.float64)
        centered_data = flat_image - color_mean
        processed_flat = (transform_matrix @ centered_data.T).T
        processed_flat += color_mean
        return processed_flat.reshape(original_shape)
    
    def apply_invert(self, image: np.ndarray, invert_mode: str = 'full', 
                    preserve_hue: bool = False, selective_channels: Optional[list] = None) -> np.ndarray:
        """
        Apply inversion to image using ImageJ-compatible algorithm.
        
        Args:
            image: Input image array
            invert_mode: 'full' | 'luminance_only' | 'selective'
            preserve_hue: Whether to preserve hue information
            selective_channels: For selective mode, list of channels to invert
        
        Returns:
            Inverted image array
        """
        self.invert_processor.invert_mode = invert_mode
        self.invert_processor.preserve_hue = preserve_hue
        return self.invert_processor.process(image, selective_channels)
    
    def apply_auto_contrast(self, image: np.ndarray, clip_percentage: float = 0.1, 
                           preserve_colors: bool = True) -> np.ndarray:
        """
        Apply auto contrast enhancement using DStretch's lEnhance algorithm.
        
        Args:
            image: Input image array
            clip_percentage: Percentage of pixels to ignore at extremes (0.0-5.0)
            preserve_colors: Whether to preserve color relationships during stretch
        
        Returns:
            Auto contrast enhanced image array
        """
        self.auto_contrast_processor.clip_percentage = clip_percentage
        self.auto_contrast_processor.preserve_colors = preserve_colors
        return self.auto_contrast_processor.process(image)
    
    def get_contrast_statistics(self, image: np.ndarray) -> dict:
        """
        Get statistics about image contrast for analysis.
        
        Args:
            image: Input image array
            
        Returns:
            Dictionary with contrast statistics
        """
        return self.auto_contrast_processor.get_contrast_statistics(image)