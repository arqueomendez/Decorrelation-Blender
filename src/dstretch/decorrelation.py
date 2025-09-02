"""
Core decorrelation stretch algorithm implementation.

This module contains the main algorithm that replicates the DStretch ImageJ plugin
functionality for archaeological rock art enhancement.
"""

import numpy as np
from scipy.linalg import eigh
from typing import Tuple, Optional, Union
import cv2
from .colorspaces import ColorspaceManager


class ProcessingResult:
    """Container for processing results and metadata."""
    
    def __init__(self, processed_image: np.ndarray, original_image: np.ndarray, 
                 colorspace: str, scale: float, transform_matrix: np.ndarray = None):
        self.processed_image = processed_image
        self.original_image = original_image
        self.colorspace = colorspace
        self.scale = scale
        self.transform_matrix = transform_matrix
        
    def save(self, filepath: str):
        """Save processed image to file."""
        cv2.imwrite(filepath, cv2.cvtColor(self.processed_image, cv2.COLOR_RGB2BGR))


class DecorrelationStretch:
    """
    Main class implementing the DStretch decorrelation stretch algorithm.
    
    Replicates the exact functionality of the ImageJ DStretch plugin by Jon Harman,
    including all 19 color spaces and the same mathematical operations.
    """
    
    def __init__(self):
        self.colorspace_manager = ColorspaceManager()
        self._last_original = None
        self._last_processed = None
    
    def process(
        self,
        image: np.ndarray,
        colorspace: str = "YDS",
        scale: float = 15.0,
        selection_mask: Optional[np.ndarray] = None
    ) -> ProcessingResult:
        """
        Apply decorrelation stretch to an image.
        
        Args:
            image: Input RGB image as numpy array (H, W, 3), dtype uint8
            colorspace: Color space name (e.g., 'YDS', 'CRGB', 'LRE')
            scale: Enhancement intensity factor (1.0 - 100.0)
            selection_mask: Optional boolean mask for area selection
            
        Returns:
            ProcessingResult object containing processed image and metadata
            
        Raises:
            ValueError: If image format is invalid or colorspace unknown
        """
        # Validate inputs
        self._validate_inputs(image, colorspace, scale)
        
        # Store original for potential reset
        self._last_original = image.copy()
        
        # Step 1: Transform to target colorspace
        colorspace_obj = self.colorspace_manager.get_colorspace(colorspace)
        transformed_image = colorspace_obj.to_colorspace(image)
        
        # Step 2: Calculate statistics (covariance matrix)
        analysis_data = self._get_analysis_data(transformed_image, selection_mask)
        covariance_matrix = self._calculate_covariance_matrix(analysis_data)
        
        # Step 3: Eigendecomposition
        eigenvalues, eigenvectors = self._eigendecomposition(covariance_matrix)
        
        # Step 4: Build transformation matrix
        transform_matrix = self._build_transform_matrix(
            eigenvectors, eigenvalues, scale
        )
        
        # Step 5: Apply transformation to entire image
        processed_transformed = self._apply_transformation(
            transformed_image, transform_matrix
        )
        
        # Step 6: Transform back to RGB
        processed_rgb = colorspace_obj.from_colorspace(processed_transformed)
        
        # Store result
        self._last_processed = processed_rgb
        
        return ProcessingResult(
            processed_image=processed_rgb,
            original_image=image,
            colorspace=colorspace,
            scale=scale,
            transform_matrix=transform_matrix
        )
    
    def reset_to_original(self) -> Optional[np.ndarray]:
        """
        Return the last original image processed.
        
        Returns:
            Original image array or None if no image has been processed
        """
        return self._last_original.copy() if self._last_original is not None else None
    
    def _validate_inputs(self, image: np.ndarray, colorspace: str, scale: float):
        """Validate input parameters."""
        if not isinstance(image, np.ndarray):
            raise ValueError("Image must be a numpy array")
        
        if image.ndim != 3 or image.shape[2] != 3:
            raise ValueError("Image must be RGB with shape (H, W, 3)")
        
        if image.dtype != np.uint8:
            raise ValueError("Image must be uint8 format")
        
        if not self.colorspace_manager.is_available(colorspace):
            available = self.colorspace_manager.list_available()
            raise ValueError(f"Unknown colorspace '{colorspace}'. Available: {list(available.keys())}")
        
        if not 1.0 <= scale <= 100.0:
            raise ValueError("Scale must be between 1.0 and 100.0")
    
    def _get_analysis_data(
        self, 
        transformed_image: np.ndarray, 
        selection_mask: Optional[np.ndarray]
    ) -> np.ndarray:
        """
        Get pixel data for statistical analysis.
        
        If selection_mask is provided, only analyze pixels in the selected area.
        Otherwise, analyze entire image.
        """
        if selection_mask is not None:
            if selection_mask.shape[:2] != transformed_image.shape[:2]:
                raise ValueError("Selection mask must match image dimensions")
            
            # Extract pixels only from selected area
            masked_pixels = transformed_image[selection_mask]
            return masked_pixels.reshape(-1, 3)
        else:
            # Use entire image
            return transformed_image.reshape(-1, 3)
    
    def _calculate_covariance_matrix(self, pixel_data: np.ndarray) -> np.ndarray:
        """Calculate 3x3 covariance matrix from pixel data."""
        # Convert to float64 for precision
        data = pixel_data.astype(np.float64)
        
        # Calculate covariance matrix
        # numpy.cov expects features as rows, observations as columns
        covariance = np.cov(data.T)
        
        return covariance
    
    def _eigendecomposition(self, covariance_matrix: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Perform eigendecomposition of covariance matrix.
        
        Returns:
            Tuple of (eigenvalues, eigenvectors)
        """
        # Use scipy's eigh for symmetric matrices (covariance is symmetric)
        # eigh returns eigenvalues in ascending order
        eigenvalues, eigenvectors = eigh(covariance_matrix)
        
        # Sort in descending order (largest eigenvalue first)
        idx = np.argsort(eigenvalues)[::-1]
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]
        
        return eigenvalues, eigenvectors
    
    def _build_transform_matrix(
        self,
        eigenvectors: np.ndarray,
        eigenvalues: np.ndarray,
        scale: float
    ) -> np.ndarray:
        """
        Build the final transformation matrix using eigenvectors/values and scale factor.
        
        This follows the DStretch algorithm exactly:
        - Scale factor affects the stretching intensity
        - Higher scale = more dramatic enhancement
        """
        # Normalize eigenvalues
        max_eigenval = np.max(eigenvalues)
        normalized_eigenvals = eigenvalues / max_eigenval
        
        # Avoid division by zero
        normalized_eigenvals = np.maximum(normalized_eigenvals, 1e-10)
        
        # Calculate scaling factors based on DStretch formula
        # Scale factor converts 1-100 range to appropriate mathematical scaling
        scale_factor = scale / 100.0
        
        # DStretch scaling: stretch inversely proportional to sqrt of eigenvalue
        stretch_factors = 1.0 + scale_factor * (1.0 / np.sqrt(normalized_eigenvals) - 1.0)
        
        # Build diagonal scaling matrix
        scaling_matrix = np.diag(stretch_factors)
        
        # Final transformation: V * S * V^T
        transform_matrix = eigenvectors @ scaling_matrix @ eigenvectors.T
        
        return transform_matrix
    
    def _apply_transformation(
        self,
        transformed_image: np.ndarray,
        transform_matrix: np.ndarray
    ) -> np.ndarray:
        """Apply transformation matrix to entire image."""
        original_shape = transformed_image.shape
        
        # Flatten image to (N_pixels, 3)
        flat_image = transformed_image.reshape(-1, 3).astype(np.float64)
        
        # Apply transformation: each pixel = matrix @ pixel
        processed_flat = (transform_matrix @ flat_image.T).T
        
        # Reshape back to image
        processed_image = processed_flat.reshape(original_shape)
        
        return processed_image


def process_image(
    image_path: str,
    colorspace: str = "YDS",
    scale: float = 15.0,
    output_path: Optional[str] = None
) -> ProcessingResult:
    """
    Convenience function to process a single image file.
    
    Args:
        image_path: Path to input image
        colorspace: Color space name
        scale: Enhancement intensity
        output_path: Optional output path (if None, doesn't save)
        
    Returns:
        ProcessingResult object
    """
    # Load image
    image_bgr = cv2.imread(image_path)
    if image_bgr is None:
        raise ValueError(f"Could not load image from {image_path}")
    
    # Convert BGR to RGB
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    
    # Process
    dstretch = DecorrelationStretch()
    result = dstretch.process(image_rgb, colorspace, scale)
    
    # Save if requested
    if output_path:
        result.save(output_path)
    
    return result