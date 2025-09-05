"""
DStretch GUI - Graphical User Interface
=======================================

Tkinter-based GUI that replicates the ImageJ DStretch plugin interface
with support for the new independent preprocessing pipeline.

Author: Claude Sonnet 4 (Based on ImageJ DStretch v6.3 by Jon Harman)
Version: 2.0
Date: January 2025
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
from PIL import Image, ImageTk
import cv2
from pathlib import Path
import threading
import logging
from typing import Optional, Dict, Any, List

# Import DStretch components
from .decorrelation import DecorrelationStretch
from .independent_processors import (
    PreprocessingPipeline, create_preprocessing_config, quick_enhance
)
from . import list_available_colorspaces, get_pipeline_info, get_available_processors

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import advanced GUI components (optional)
try:
    from .gui_infrastructure import GUIInfrastructure, AdvancedStatusBar
    from .pixel_inspector import PixelInspectorPanel
    from .zoom_pan_controller import ZoomPanController
    ADVANCED_GUI_AVAILABLE = True
except ImportError:
    ADVANCED_GUI_AVAILABLE = False
    logger.info("Advanced GUI components not available, using basic interface")


class DStretchGUI:
    """
    Main DStretch GUI application.
    Replicates the ImageJ DStretch interface with new pipeline architecture.
    """
    
    def __init__(self):
        """Initialize the GUI application."""
        self.root = tk.Tk()
        self.root.title("DStretch Python v2.0 - Independent Pipeline")
        self.root.geometry("1000x700")
        
        # Core components
        self.dstretch = DecorrelationStretch()
        self.preprocessing_pipeline = PreprocessingPipeline()
        
        # Image data
        self.original_image = None
        self.processed_image = None
        self.preprocessed_image = None
        self.last_result = None
        
        # GUI state
        self.current_colorspace = "YDS"
        self.processing_thread = None
        
        # Initialize status_var FIRST
        self.status_var = tk.StringVar()
        
        # Advanced GUI infrastructure (if available)
        self.infrastructure = None
        self.status_bar = None
        self.pixel_inspector = None
        self.zoom_controller = None
        
        # Set up GUI
        self._setup_ui()
        self._setup_menu()
        
        # Initialize status AFTER UI setup
        self._set_status("Ready - Load an image to begin")
        
        logger.info("DStretch GUI initialized successfully")
    
    def _setup_ui(self):
        """Set up the main user interface."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel: Image display
        left_frame = ttk.LabelFrame(main_frame, text="Image", padding=5)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Image canvas
        self.canvas = tk.Canvas(left_frame, bg='gray90', width=500, height=400)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Right panel: Controls
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        self._setup_file_controls(right_frame)
        self._setup_preprocessing_controls(right_frame)
        self._setup_colorspace_controls(right_frame)
        self._setup_processing_controls(right_frame)
        
        # Status bar (use existing status_var)
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)
        ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN).pack(fill=tk.X)
    
    def _setup_file_controls(self, parent):
        """Set up file operation controls."""
        file_frame = ttk.LabelFrame(parent, text="File Operations", padding=5)
        file_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(file_frame, text="Open Image", 
                  command=self._open_image).pack(fill=tk.X, pady=2)
        ttk.Button(file_frame, text="Save Result", 
                  command=self._save_image).pack(fill=tk.X, pady=2)
        
        # Reset button
        self.reset_button = ttk.Button(file_frame, text="Reset to Original", 
                                      command=self._reset_image, state=tk.DISABLED)
        self.reset_button.pack(fill=tk.X, pady=2)
    
    def _setup_preprocessing_controls(self, parent):
        """Set up preprocessing controls."""
        preprocess_frame = ttk.LabelFrame(parent, text="Preprocessing", padding=5)
        preprocess_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Preset selection
        ttk.Label(preprocess_frame, text="Preset:").pack(anchor=tk.W)
        self.preset_var = tk.StringVar(value="custom")
        preset_combo = ttk.Combobox(preprocess_frame, textvariable=self.preset_var,
                                   values=["custom", "standard", "faint_reds", "yellows", "high_contrast"],
                                   state="readonly")
        preset_combo.pack(fill=tk.X, pady=(0, 5))
        preset_combo.bind("<<ComboboxSelected>>", self._on_preset_changed)
        
        # Individual preprocessing options
        self.invert_var = tk.BooleanVar()
        ttk.Checkbutton(preprocess_frame, text="Invert", 
                       variable=self.invert_var).pack(anchor=tk.W)
        
        self.auto_contrast_var = tk.BooleanVar()
        ttk.Checkbutton(preprocess_frame, text="Auto Contrast", 
                       variable=self.auto_contrast_var).pack(anchor=tk.W)
        
        self.color_balance_var = tk.BooleanVar()
        ttk.Checkbutton(preprocess_frame, text="Color Balance", 
                       variable=self.color_balance_var).pack(anchor=tk.W)
        
        self.flatten_var = tk.BooleanVar()
        ttk.Checkbutton(preprocess_frame, text="Flatten Illumination", 
                       variable=self.flatten_var).pack(anchor=tk.W)
        
        # Advanced preprocessing options
        advanced_frame = ttk.LabelFrame(preprocess_frame, text="Advanced Options", padding=2)
        advanced_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Auto Contrast options
        ttk.Label(advanced_frame, text="Contrast Clip %:", font=("TkDefaultFont", 8)).pack(anchor=tk.W)
        self.contrast_clip_var = tk.DoubleVar(value=0.1)
        ttk.Scale(advanced_frame, from_=0.0, to=2.0, variable=self.contrast_clip_var,
                 orient=tk.HORIZONTAL).pack(fill=tk.X)
        
        # Color Balance options
        ttk.Label(advanced_frame, text="Balance Method:", font=("TkDefaultFont", 8)).pack(anchor=tk.W)
        self.balance_method_var = tk.StringVar(value="gray_world")
        ttk.Combobox(advanced_frame, textvariable=self.balance_method_var,
                    values=["gray_world", "white_patch", "manual"],
                    state="readonly", font=("TkDefaultFont", 8)).pack(fill=tk.X)
        
        ttk.Label(advanced_frame, text="Balance Strength:", font=("TkDefaultFont", 8)).pack(anchor=tk.W)
        self.balance_strength_var = tk.DoubleVar(value=1.0)
        ttk.Scale(advanced_frame, from_=0.0, to=2.0, variable=self.balance_strength_var,
                 orient=tk.HORIZONTAL).pack(fill=tk.X)
        
        # Flatten options
        ttk.Label(advanced_frame, text="Flatten Method:", font=("TkDefaultFont", 8)).pack(anchor=tk.W)
        self.flatten_method_var = tk.StringVar(value="bandpass")
        ttk.Combobox(advanced_frame, textvariable=self.flatten_method_var,
                    values=["bandpass", "gaussian", "sliding_paraboloid", "rolling_ball"],
                    state="readonly", font=("TkDefaultFont", 8)).pack(fill=tk.X)
        
        ttk.Label(advanced_frame, text="Large Structures:", font=("TkDefaultFont", 8)).pack(anchor=tk.W)
        self.flatten_large_var = tk.DoubleVar(value=40.0)
        ttk.Scale(advanced_frame, from_=10.0, to=100.0, variable=self.flatten_large_var,
                 orient=tk.HORIZONTAL).pack(fill=tk.X)
        
        ttk.Label(advanced_frame, text="Small Structures:", font=("TkDefaultFont", 8)).pack(anchor=tk.W)
        self.flatten_small_var = tk.DoubleVar(value=3.0)
        ttk.Scale(advanced_frame, from_=1.0, to=10.0, variable=self.flatten_small_var,
                 orient=tk.HORIZONTAL).pack(fill=tk.X)
    
    def _setup_colorspace_controls(self, parent):
        """Set up colorspace selection controls."""
        colorspace_frame = ttk.LabelFrame(parent, text="Color Spaces", padding=5)
        colorspace_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Get available colorspaces
        self.colorspaces = list_available_colorspaces()
        self.colorspace_buttons = {}
        
        # Create colorspace button grid (replicating ImageJ DStretch layout)
        button_layout = [
            ['YDS', 'YBR', 'YBK', 'YRE'],
            ['YRD', 'YWE', 'YBL', 'YBG'],
            ['YUV', 'YYE', 'LAX', 'LDS'],
            ['LRE', 'LRD', 'LBK', 'LBL'],
            ['LWE', 'LYE', 'RGB', 'LAB'],
            ['CRGB', 'RGB0', 'LABI', '']
        ]
        
        for row_idx, row in enumerate(button_layout):
            row_frame = ttk.Frame(colorspace_frame)
            row_frame.pack(fill=tk.X, pady=1)
            
            for col_idx, cs_name in enumerate(row):
                if cs_name and cs_name in self.colorspaces:
                    btn = ttk.Button(
                        row_frame, text=cs_name, width=6,
                        command=lambda name=cs_name: self._select_colorspace(name)
                    )
                    btn.pack(side=tk.LEFT, padx=1, fill=tk.X, expand=True)
                    self.colorspace_buttons[cs_name] = btn
                elif cs_name:
                    ttk.Frame(row_frame, width=50).pack(side=tk.LEFT, padx=1)
        
        # Highlight default colorspace
        self._select_colorspace(self.current_colorspace)
    
    def _setup_processing_controls(self, parent):
        """Set up main processing controls."""
        process_frame = ttk.LabelFrame(parent, text="Processing", padding=5)
        process_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Scale control
        ttk.Label(process_frame, text="Scale:").pack(anchor=tk.W)
        self.scale_var = tk.DoubleVar(value=15.0)
        scale_frame = ttk.Frame(process_frame)
        scale_frame.pack(fill=tk.X, pady=2)
        
        ttk.Scale(scale_frame, from_=1.0, to=100.0, variable=self.scale_var,
                 orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        scale_label = ttk.Label(scale_frame, text="15", width=4)
        scale_label.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Update scale label
        def update_scale_label(*args):
            scale_label.config(text=f"{int(self.scale_var.get())}")
        self.scale_var.trace('w', update_scale_label)
        
        # Main process button
        self.process_button = ttk.Button(
            process_frame, text="Process Image", 
            command=self._process_image, state=tk.DISABLED
        )
        self.process_button.pack(fill=tk.X, pady=(10, 5))
        
        # Individual processor buttons
        individual_frame = ttk.LabelFrame(process_frame, text="Individual Tools", padding=2)
        individual_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Row 1: Invert and Auto Contrast
        row1 = ttk.Frame(individual_frame)
        row1.pack(fill=tk.X, pady=1)
        ttk.Button(row1, text="Invert Only", 
                  command=self._apply_invert_only).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,2))
        ttk.Button(row1, text="Auto Contrast", 
                  command=self._apply_auto_contrast_only).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2,0))
        
        # Row 2: Color Balance and Flatten
        row2 = ttk.Frame(individual_frame)
        row2.pack(fill=tk.X, pady=1)
        ttk.Button(row2, text="Color Balance", 
                  command=self._apply_color_balance_only).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,2))
        ttk.Button(row2, text="Flatten", 
                  command=self._apply_flatten_only).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2,0))
        
        # Row 3: Hue Shift and Quick Enhance
        row3 = ttk.Frame(individual_frame)
        row3.pack(fill=tk.X, pady=1)
        ttk.Button(row3, text="Hue Shift", 
                  command=self._apply_hue_shift_only).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,2))
        ttk.Button(row3, text="Quick Enhance", 
                  command=self._quick_enhance).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2,0))
    
    def _setup_menu(self):
        """Set up application menu."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Image...", command=self._open_image)
        file_menu.add_command(label="Save Result...", command=self._save_image)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Pipeline Info", command=self._show_pipeline_info)
        tools_menu.add_command(label="Available Processors", command=self._show_processors)
        tools_menu.add_separator()
        tools_menu.add_command(label="Reset All Settings", command=self._reset_all_settings)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
    
    # Event handlers
    
    def _on_preset_changed(self, event=None):
        """Handle preset selection change."""
        preset = self.preset_var.get()
        if preset == "custom":
            return
        
        # Apply preset configurations
        preset_configs = {
            "standard": {
                "auto_contrast": True,
                "color_balance": True,
                "contrast_clip": 0.1,
                "balance_strength": 0.8
            },
            "faint_reds": {
                "auto_contrast": True,
                "color_balance": True,
                "contrast_clip": 0.05,
                "balance_strength": 1.0
            },
            "yellows": {
                "auto_contrast": True,
                "flatten": True,
                "contrast_clip": 0.2,
                "flatten_method": "bandpass"
            },
            "high_contrast": {
                "auto_contrast": True,
                "contrast_clip": 0.5,
                "balance_strength": 1.2
            }
        }
        
        if preset in preset_configs:
            config = preset_configs[preset]
            
            # Reset all
            self.auto_contrast_var.set(config.get("auto_contrast", False))
            self.color_balance_var.set(config.get("color_balance", False))
            self.flatten_var.set(config.get("flatten", False))
            self.invert_var.set(config.get("invert", False))
            
            # Advanced options
            self.contrast_clip_var.set(config.get("contrast_clip", 0.1))
            self.balance_strength_var.set(config.get("balance_strength", 1.0))
            if "flatten_method" in config:
                self.flatten_method_var.set(config["flatten_method"])
            
            self._set_status(f"Applied {preset} preset")
    
    def _select_colorspace(self, colorspace_name):
        """Select a colorspace and update UI."""
        if colorspace_name not in self.colorspaces:
            return
        
        # Update current selection
        self.current_colorspace = colorspace_name
        
        # Update button text to show selection
        for name, button in self.colorspace_buttons.items():
            if name == colorspace_name:
                button.configure(text=f"[{name}]")
            else:
                button.configure(text=name)
        
        self._set_status(f"Selected colorspace: {colorspace_name}")
    
    # Image operations
    
    def _open_image(self):
        """Open an image file."""
        file_types = [
            ("Image files", "*.jpg *.jpeg *.png *.tiff *.tif *.bmp"),
            ("JPEG files", "*.jpg *.jpeg"),
            ("PNG files", "*.png"),
            ("TIFF files", "*.tiff *.tif"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Open Image",
            filetypes=file_types
        )
        
        if filename:
            try:
                # Load image
                pil_image = Image.open(filename)
                
                # Convert to RGB if necessary
                if pil_image.mode != 'RGB':
                    pil_image = pil_image.convert('RGB')
                
                # Convert to numpy array
                self.original_image = np.array(pil_image)
                self.processed_image = self.original_image.copy()
                self.preprocessed_image = None
                self.last_result = None
                
                # Display image
                self._display_image(self.original_image)
                
                # Update UI state
                self._update_ui_state()
                
                self._set_status(f"Loaded: {Path(filename).name} ({self.original_image.shape[1]}x{self.original_image.shape[0]})")
                
            except Exception as e:
                messagebox.showerror("Open Error", f"Could not open image:\n{e}")
    
    def _save_image(self):
        """Save the processed image."""
        if self.processed_image is None:
            messagebox.showwarning("Save Warning", "No processed image to save")
            return
        
        # Suggest filename
        default_name = f"enhanced_{self.current_colorspace}_scale{int(self.scale_var.get())}.jpg"
        
        file_types = [
            ("JPEG files", "*.jpg"),
            ("PNG files", "*.png"),
            ("TIFF files", "*.tiff"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.asksaveasfilename(
            title="Save Enhanced Image",
            initialname=default_name,
            filetypes=file_types,
            defaultextension='.jpg'
        )
        
        if filename:
            try:
                pil_image = Image.fromarray(self.processed_image)
                pil_image.save(filename)
                self._set_status(f"Saved: {Path(filename).name}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Could not save image:\n{e}")
    
    def _reset_image(self):
        """Reset to original image."""
        if self.original_image is not None:
            self.processed_image = self.original_image.copy()
            self.preprocessed_image = None
            self.last_result = None
            self._display_image(self.processed_image)
            self._update_ui_state()
            self._set_status("Reset to original image")
    
    def _display_image(self, image):
        """Display an image on the canvas."""
        if image is None:
            return
        
        # Calculate display size (fit to canvas)
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            # Canvas not ready, schedule for later
            self.root.after(100, lambda: self._display_image(image))
            return
        
        img_height, img_width = image.shape[:2]
        
        # Calculate scaling factor
        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        scale = min(scale_x, scale_y, 1.0)  # Don't upscale
        
        # Resize image for display
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        display_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        # Convert to PIL and then to PhotoImage
        pil_image = Image.fromarray(display_image)
        self.photo_image = ImageTk.PhotoImage(pil_image)
        
        # Clear canvas and display image
        self.canvas.delete("all")
        self.canvas.create_image(
            canvas_width // 2, canvas_height // 2,
            image=self.photo_image, anchor=tk.CENTER
        )
    
    # Processing operations
    
    def _process_image(self):
        """Process image with current settings."""
        if self.original_image is None:
            messagebox.showwarning("Process Warning", "No image loaded")
            return
        
        # Disable processing button during operation
        self.process_button.configure(state=tk.DISABLED)
        self._set_status("Processing...")
        
        # Start processing in separate thread
        self.processing_thread = threading.Thread(target=self._process_image_thread)
        self.processing_thread.daemon = True
        self.processing_thread.start()
    
    def _process_image_thread(self):
        """Process image in separate thread."""
        try:
            # Build preprocessing config
            config = self._build_preprocessing_config()
            
            # Apply preprocessing if any steps are enabled
            if any(step.get('enabled', False) for step in config.values()):
                self.preprocessed_image, preprocessing_results = self.preprocessing_pipeline.process(
                    self.original_image, config
                )
                
                # Use preprocessed image for decorrelation
                input_image = self.preprocessed_image
                self._set_status_threadsafe("Preprocessing completed, applying decorrelation...")
            else:
                # No preprocessing, use original image
                input_image = self.original_image
                preprocessing_results = []
                self.preprocessed_image = None
            
            # Apply decorrelation stretch
            self.last_result = self.dstretch.process(
                input_image, 
                self.current_colorspace, 
                self.scale_var.get()
            )
            
            self.processed_image = self.last_result.processed_image
            
            # Update UI in main thread
            self.root.after(0, self._processing_completed)
            
        except Exception as e:
            logger.error(f"Processing error: {e}")
            self.root.after(0, lambda: self._processing_failed(str(e)))
    
    def _build_preprocessing_config(self):
        """Build preprocessing configuration from UI state."""
        config = {}
        
        if self.auto_contrast_var.get():
            config['auto_contrast'] = {
                'enabled': True,
                'saturated_pixels': self.contrast_clip_var.get(),
                'normalize': True
            }
        
        if self.color_balance_var.get():
            config['color_balance'] = {
                'enabled': True,
                'method': self.balance_method_var.get(),
                'strength': self.balance_strength_var.get(),
                'preserve_luminance': True
            }
        
        if self.flatten_var.get():
            config['flatten'] = {
                'enabled': True,
                'method': self.flatten_method_var.get(),
                'large_structures': int(self.flatten_large_var.get()),
                'small_structures': int(self.flatten_small_var.get()),
                'auto_scale': True
            }
        
        if self.invert_var.get():
            config['invert'] = {
                'enabled': True
            }
        
        return config
    
    def _quick_enhance(self):
        """Apply quick enhancement based on current colorspace."""
        if self.original_image is None:
            messagebox.showwarning("Process Warning", "No image loaded")
            return
        
        try:
            self._set_status("Applying quick enhancement...")
            
            # Apply quick enhancement
            enhanced_image = quick_enhance(self.original_image, 'balanced')
            
            # Apply decorrelation stretch
            self.last_result = self.dstretch.process(
                enhanced_image, 
                self.current_colorspace, 
                self.scale_var.get()
            )
            
            self.processed_image = self.last_result.processed_image
            self.preprocessed_image = enhanced_image
            
            # Update display
            self._display_image(self.processed_image)
            self._update_ui_state()
            
            self._set_status("Quick enhancement applied")
            
        except Exception as e:
            messagebox.showerror("Enhancement Error", f"Quick enhancement failed:\n{e}")
    
    # Individual processor methods
    
    def _apply_invert_only(self):
        """Apply invert processor only (no decorrelation)."""
        self._apply_single_processor('invert', 'Invert')
    
    def _apply_auto_contrast_only(self):
        """Apply auto contrast processor only (no decorrelation)."""
        config = {
            'saturated_pixels': self.contrast_clip_var.get(),
            'normalize': True
        }
        self._apply_single_processor('auto_contrast', 'Auto Contrast', config)
    
    def _apply_color_balance_only(self):
        """Apply color balance processor only (no decorrelation)."""
        config = {
            'method': self.balance_method_var.get(),
            'strength': self.balance_strength_var.get(),
            'preserve_luminance': True
        }
        self._apply_single_processor('color_balance', 'Color Balance', config)
    
    def _apply_flatten_only(self):
        """Apply flatten processor only (no decorrelation)."""
        config = {
            'method': self.flatten_method_var.get(),
            'large_structures': int(self.flatten_large_var.get()),
            'small_structures': int(self.flatten_small_var.get()),
            'suppress_stripes': True,
            'auto_scale': True
        }
        self._apply_single_processor('flatten', 'Flatten', config)
    
    def _apply_hue_shift_only(self):
        """Apply hue shift processor only (no decorrelation)."""
        # Simple dialog for hue shift amount
        from tkinter import simpledialog
        
        hue_shift = simpledialog.askfloat(
            "Hue Shift",
            "Enter hue shift in degrees (-180 to 180):",
            initialvalue=0,
            minvalue=-180,
            maxvalue=180
        )
        
        if hue_shift is not None:
            config = {
                'hue_shift': hue_shift,
                'saturation_boost': 1.0,
                'selective': False
            }
            self._apply_single_processor('hue_shift', 'Hue Shift', config)
    
    def _apply_single_processor(self, processor_name: str, display_name: str, config: dict = None):
        """Apply a single processor independently."""
        if self.original_image is None:
            messagebox.showwarning("Process Warning", "No image loaded")
            return
        
        try:
            self._set_status(f"Applying {display_name}...")
            
            # Import processor factory
            from .independent_processors import ProcessorFactory, ProcessorType
            
            # Get processor type
            processor_type_map = {
                'invert': ProcessorType.INVERT,
                'auto_contrast': ProcessorType.AUTO_CONTRAST,
                'color_balance': ProcessorType.COLOR_BALANCE,
                'flatten': ProcessorType.FLATTEN,
                'hue_shift': ProcessorType.HUE_SHIFT
            }
            
            if processor_name not in processor_type_map:
                raise ValueError(f"Unknown processor: {processor_name}")
            
            # Create processor and apply
            processor_type = processor_type_map[processor_name]
            processor = ProcessorFactory.create_processor(processor_type)
            
            # Apply processor with config
            result = processor.process(self.original_image, **(config or {}))
            
            # Update display with processed image
            self.processed_image = result.image
            self.preprocessed_image = result.image  # Store as preprocessed
            self.last_result = None  # No decorrelation applied
            
            # Update display
            self._display_image(self.processed_image)
            self._update_ui_state()
            
            # Show statistics if available
            if result.statistics:
                stats_info = f"{display_name} applied successfully\n\n"
                if 'overall_improvement' in result.statistics:
                    stats_info += f"Improvement: {result.statistics['overall_improvement']:.2f}\n"
                messagebox.showinfo(f"{display_name} Results", stats_info)
            
            self._set_status(f"{display_name} applied (independent)")
            
        except Exception as e:
            messagebox.showerror(f"{display_name} Error", f"{display_name} failed:\n{e}")
    
    def _processing_completed(self):
        """Handle successful processing completion."""
        # Update display
        self._display_image(self.processed_image)
        
        # Update UI state
        self._update_ui_state()
        
        # Re-enable processing button
        self.process_button.configure(state=tk.NORMAL)
        
        # Update status
        preprocessing_info = " (with preprocessing)" if self.preprocessed_image is not None else ""
        self._set_status(f"Processing completed: {self.current_colorspace} scale {int(self.scale_var.get())}{preprocessing_info}")
    
    def _processing_failed(self, error_message):
        """Handle processing failure."""
        # Re-enable processing button
        self.process_button.configure(state=tk.NORMAL)
        
        # Show error
        messagebox.showerror("Processing Error", f"Processing failed:\n{error_message}")
        
        self._set_status("Processing failed")
    
    def _set_status_threadsafe(self, message):
        """Set status message from thread."""
        self.root.after(0, lambda: self._set_status(message))
    
    # Menu handlers
    
    def _show_pipeline_info(self):
        """Show pipeline information dialog."""
        info = get_pipeline_info()
        info_text = "DStretch Pipeline Information:\n\n"
        for key, value in info.items():
            info_text += f"{key}: {value}\n"
        
        messagebox.showinfo("Pipeline Information", info_text)
    
    def _show_processors(self):
        """Show available processors dialog."""
        processors = get_available_processors()
        processor_text = "Available Processors:\n\n"
        for processor_type in processors:
            processor_text += f"• {processor_type.value}\n"
        
        messagebox.showinfo("Available Processors", processor_text)
    
    def _reset_all_settings(self):
        """Reset all settings to defaults."""
        self.preset_var.set("custom")
        self.invert_var.set(False)
        self.auto_contrast_var.set(False)
        self.color_balance_var.set(False)
        self.flatten_var.set(False)
        self.contrast_clip_var.set(0.1)
        self.balance_method_var.set("gray_world")
        self.balance_strength_var.set(1.0)
        self.flatten_method_var.set("bandpass")
        self.flatten_large_var.set(40.0)
        self.flatten_small_var.set(3.0)
        self.scale_var.set(15.0)
        self._select_colorspace("YDS")
        self._set_status("Settings reset to defaults")
    
    def _show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About DStretch Python v2.0",
            "DStretch Python v2.0\n"
            "Independent Pipeline Architecture\n\n"
            "Python implementation of the DStretch decorrelation stretch algorithm\n"
            "for enhancing archaeological rock art images.\n\n"
            "NEW in v2.0:\n"
            "• Independent preprocessing pipeline\n"
            "• Corrected tool application order\n"
            "• Enhanced presets for common use cases\n"
            "• Improved workflow matching ImageJ DStretch\n\n"
            "Based on the original DStretch ImageJ plugin by Jon Harman.\n"
            "Python implementation by Claude (DStretch Migration Project)."
        )
    
    # Utility methods
    
    def _set_status(self, message):
        """Set status message."""
        self.status_var.set(message)
    
    def _update_ui_state(self):
        """Update UI state based on current conditions."""
        has_image = self.original_image is not None
        has_result = self.last_result is not None
        
        # Enable/disable buttons
        self.process_button.configure(state=tk.NORMAL if has_image else tk.DISABLED)
        self.reset_button.configure(state=tk.NORMAL if has_result else tk.DISABLED)
    
    def run(self):
        """Start the GUI application."""
        self.root.mainloop()


def main():
    """Main entry point for GUI application."""
    try:
        app = DStretchGUI()
        app.run()
    except Exception as e:
        # Fallback error handling
        import tkinter.messagebox as mb
        mb.showerror(
            "Startup Error",
            f"Failed to start DStretch GUI:\n{e}\n\n"
            f"Advanced GUI available: {ADVANCED_GUI_AVAILABLE}"
        )


if __name__ == '__main__':
    main()