"""
Graphical user interface for DStretch Python.

Replicates the DStretch ImageJ plugin interface using Tkinter,
providing the same workflow and visual layout.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
from pathlib import Path
import threading
from typing import Optional

from . import DecorrelationStretch, list_available_colorspaces as get_available_colorspaces
from .pixel_inspector import PixelInspectorPanel
from .zoom_pan_controller import ZoomPanController, ZoomToolbar
from .gui_infrastructure import GUIInfrastructure, AdvancedStatusBar


class DStretchGUI:
    """Main GUI application for DStretch."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("DStretch Python")
        self.root.geometry("1200x700")  # Increased width for inspector panel
        self.root.minsize(900, 500)  # Adjusted minimum size
        
        # Application state
        self.dstretch = DecorrelationStretch()
        self.original_image = None
        self.processed_image = None
        self.current_colorspace = "YDS"
        self.current_scale = 15.0
        
        # Initialize infrastructure
        self.infrastructure = GUIInfrastructure(self.root)
        
        # UI components
        self.image_display = None
        self.colorspace_buttons = {}
        self.scale_var = None
        self.status_var = None
        self.process_button = None
        self.reset_button = None
        self.pixel_inspector = None
        self.zoom_controller = None
        self.zoom_toolbar = None
        self.status_bar = None
        
        self._setup_ui()
        self._setup_menu()
        self._update_ui_state()
    
    def _setup_ui(self):
        """Setup the main user interface."""
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=2)  # Image panel gets more space
        main_frame.columnconfigure(1, weight=1)  # Control panel
        main_frame.columnconfigure(2, weight=1)  # Inspector panel
        main_frame.rowconfigure(0, weight=1)
        
        # Left panel: Image display
        self._setup_image_panel(main_frame)
        
        # Center panel: Controls
        self._setup_control_panel(main_frame)
        
        # Right panel: Pixel Inspector (after zoom controller is ready)
        self._setup_inspector_panel(main_frame)
        
        # Connect zoom controller to inspector
        if self.pixel_inspector and self.zoom_controller:
            self.pixel_inspector.set_zoom_controller(self.zoom_controller)
        
        # Bottom: Status bar
        self._setup_status_bar()
    
    def _setup_image_panel(self, parent):
        """Setup the image display panel with zoom and pan capabilities."""
        image_frame = ttk.LabelFrame(parent, text="Image", padding="5")
        image_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        # Configure grid
        image_frame.columnconfigure(0, weight=1)
        image_frame.rowconfigure(1, weight=1)  # Canvas gets the space
        
        # Create zoom toolbar
        toolbar_frame = ttk.Frame(image_frame)
        toolbar_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Canvas for image display with enhanced capabilities
        self.image_canvas = tk.Canvas(
            image_frame,
            bg='lightgray',
            width=400,
            height=300
        )
        self.image_canvas.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Initialize zoom controller
        self.zoom_controller = ZoomPanController(
            self.image_canvas,
            update_callback=self._on_zoom_pan_update
        )
        
        # Initialize zoom toolbar
        self.zoom_toolbar = ZoomToolbar(toolbar_frame, self.zoom_controller)
        self.zoom_toolbar.grid(row=0, column=0, sticky=tk.W)
        
        # Scrollbars for large images (managed by zoom controller)
        v_scrollbar = ttk.Scrollbar(image_frame, orient=tk.VERTICAL, command=self.image_canvas.yview)
        h_scrollbar = ttk.Scrollbar(image_frame, orient=tk.HORIZONTAL, command=self.image_canvas.xview)
        
        self.image_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        v_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        # Placeholder text
        self.image_canvas.create_text(
            200, 150,
            text="No image loaded\nUse File -> Open Image\n\nMouse: Wheel=Zoom, Right-drag=Pan\n(or Shift+drag)",
            font=('Arial', 12),
            fill='gray',
            tags='placeholder'
        )
    
    def _setup_control_panel(self, parent):
        """Setup the control panel with colorspace buttons and scale slider."""
        control_frame = ttk.LabelFrame(parent, text="Controls", padding="10")
        control_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        # Colorspace selection
        cs_frame = ttk.LabelFrame(control_frame, text="Color Spaces", padding="10")
        cs_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self._setup_colorspace_buttons(cs_frame)
        
        # Scale control
        scale_frame = ttk.LabelFrame(control_frame, text="Enhancement Scale", padding="10")
        scale_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.scale_var = tk.DoubleVar(value=15.0)
        scale_slider = ttk.Scale(
            scale_frame,
            from_=1.0,
            to=100.0,
            orient=tk.HORIZONTAL,
            variable=self.scale_var,
            command=self._on_scale_change
        )
        scale_slider.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Scale value display
        self.scale_label = ttk.Label(scale_frame, text="15")
        self.scale_label.grid(row=1, column=0)
        
        scale_frame.columnconfigure(0, weight=1)
        
        # Pre-processing controls
        preprocess_frame = ttk.LabelFrame(control_frame, text="Pre-Processing", padding="10")
        preprocess_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.auto_contrast_var = tk.BooleanVar()
        self.auto_contrast_check = ttk.Checkbutton(
            preprocess_frame,
            text="Auto Contrast",
            variable=self.auto_contrast_var
        )
        self.auto_contrast_check.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # Auto contrast parameters
        contrast_params_frame = ttk.Frame(preprocess_frame)
        contrast_params_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(contrast_params_frame, text="Clip %:").grid(row=0, column=0, sticky=tk.W)
        self.contrast_clip_var = tk.DoubleVar(value=0.1)
        contrast_clip_spin = ttk.Spinbox(
            contrast_params_frame,
            from_=0.0,
            to=5.0,
            increment=0.1,
            textvariable=self.contrast_clip_var,
            width=6
        )
        contrast_clip_spin.grid(row=0, column=1, sticky=tk.W, padx=(5, 10))
        
        self.preserve_colors_var = tk.BooleanVar(value=True)
        preserve_colors_check = ttk.Checkbutton(
            contrast_params_frame,
            text="Preserve Colors",
            variable=self.preserve_colors_var
        )
        preserve_colors_check.grid(row=0, column=2, sticky=tk.W)
        
        preprocess_frame.columnconfigure(0, weight=1)
        
        # Invert control
        invert_frame = ttk.LabelFrame(control_frame, text="Post-Processing", padding="10")
        invert_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.invert_var = tk.BooleanVar()
        self.invert_check = ttk.Checkbutton(
            invert_frame,
            text="Apply Inversion",
            variable=self.invert_var
        )
        self.invert_check.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.invert_mode_var = tk.StringVar(value="full")
        invert_mode_frame = ttk.Frame(invert_frame)
        invert_mode_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(invert_mode_frame, text="Mode:").grid(row=0, column=0, sticky=tk.W)
        invert_combo = ttk.Combobox(
            invert_mode_frame,
            textvariable=self.invert_mode_var,
            values=["full", "luminance_only", "selective"],
            state="readonly",
            width=12
        )
        invert_combo.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        invert_frame.columnconfigure(0, weight=1)
        
        # Action buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.process_button = ttk.Button(
            button_frame,
            text="Process Image",
            command=self._process_image,
            state=tk.DISABLED
        )
        self.process_button.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.reset_button = ttk.Button(
            button_frame,
            text="Reset to Original",
            command=self._reset_to_original,
            state=tk.DISABLED
        )
        self.reset_button.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        button_frame.columnconfigure(0, weight=1)
        control_frame.columnconfigure(0, weight=1)
    
    def _setup_inspector_panel(self, parent):
        """Setup the pixel inspector panel."""
        # Create the pixel inspector
        self.pixel_inspector = PixelInspectorPanel(parent, self.image_canvas)
        
        # Grid the inspector frame
        self.pixel_inspector.grid(
            row=0, column=2, 
            sticky=(tk.W, tk.E, tk.N, tk.S), 
            padx=(5, 0)
        )
    
    def _on_zoom_pan_update(self):
        """Callback for zoom/pan updates."""
        # Update zoom toolbar display
        if self.zoom_toolbar:
            self.zoom_toolbar.update_zoom_display()
        
        # Update status bar with zoom info
        if self.zoom_controller and self.zoom_controller.current_image and self.status_bar:
            zoom_factor = self.zoom_controller.get_zoom_factor()
            self.status_bar.set_zoom_info(zoom_factor)
    
    def _setup_colorspace_buttons(self, parent):
        """Setup the grid of colorspace buttons."""
        available_colorspaces = get_available_colorspaces()
        
        # Organize colorspaces in rows (4 buttons per row to match DStretch layout)
        colorspace_names = available_colorspaces
        rows = []
        for i in range(0, len(colorspace_names), 4):
            rows.append(colorspace_names[i:i+4])
        
        # Create buttons with tooltips
        colorspace_descriptions = {
            'YDS': 'General purpose, excellent for yellows',
            'CRGB': 'Pre-calculated matrix for faint reds',
            'LDS': 'General, better than YDS for yellows',
            'LRE': 'Excellent for reds, natural colors',
            'YBR': 'Optimized for reds',
            'YBK': 'Specialized for blacks and blues',
            'YRE': 'Extreme red enhancement',
            'YRD': 'Red pigments',
            'YWE': 'White pigments',
            'YBL': 'Blacks/greens',
            'YBG': 'Green pigments',
            'YUV': 'General purpose',
            'YYE': 'Yellows to brown',
            'LAX': 'LAB variant',
            'LRD': 'Red pigments (LAB)',
            'LBK': 'Black pigments',
            'LBL': 'Black alternative',
            'LWE': 'White pigments (LAB)',
            'LYE': 'Yellows to brown (LAB)',
            'RGB': 'Standard RGB',
            'LAB': 'CIE LAB standard',
            'RGB0': 'Built-in red enhancement',
            'LABI': 'Built-in LAB inversion'
        }
        
        for row_idx, row in enumerate(rows):
            for col_idx, cs_name in enumerate(row):
                btn = ttk.Button(
                    parent,
                    text=cs_name,
                    width=8,
                    command=lambda name=cs_name: self._select_colorspace(name)
                )
                btn.grid(row=row_idx, column=col_idx, padx=2, pady=2, sticky=tk.W+tk.E)
                self.colorspace_buttons[cs_name] = btn
                
                # Add tooltip
                if cs_name in colorspace_descriptions:
                    self.infrastructure.tooltip_manager.add_colorspace_tooltip(
                        btn, cs_name, colorspace_descriptions[cs_name]
                    )
        
        # Configure grid weights
        for i in range(4):
            parent.columnconfigure(i, weight=1)
        
        # Highlight default colorspace
        self._highlight_colorspace_button("YDS")
    
    def _setup_menu(self):
        """Setup the application menu."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        
        file_menu.add_command(label="Open Image...", command=self._open_image, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Save As...", command=self._save_image, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        help_menu.add_command(label="About", command=self._show_about)
        
        # Keyboard shortcuts
        self.root.bind('<Control-o>', lambda e: self._open_image())
        self.root.bind('<Control-s>', lambda e: self._save_image())
    
    def _setup_status_bar(self):
        """Setup the enhanced status bar."""
        self.status_bar = AdvancedStatusBar(self.root)
        self.status_bar.grid(
            row=1, column=0,
            sticky=(tk.W, tk.E),
            padx=5, pady=(0, 5)
        )
        
        # Connect infrastructure
        self.infrastructure.set_status_bar(self.status_bar)
        
        # Initialize with default values
        self.status_bar.set_main_status("Ready - Load an image to begin")
    
    def _open_image(self):
        """Open an image file."""
        file_types = [
            ('Image files', '*.jpg *.jpeg *.png *.tiff *.tif *.bmp'),
            ('JPEG files', '*.jpg *.jpeg'),
            ('PNG files', '*.png'),
            ('TIFF files', '*.tiff *.tif'),
            ('All files', '*.*')
        ]
        
        filename = filedialog.askopenfilename(
            title="Open Image",
            filetypes=file_types
        )
        
        if filename:
            try:
                self._load_image(filename)
                self.status_bar.set_main_status(f"Loaded: {Path(filename).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not load image:\n{e}")
    
    def _load_image(self, filename):
        """Load and display an image."""
        # Load image using PIL
        pil_image = Image.open(filename)
        
        # Convert to RGB if necessary
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # Store original image as numpy array
        self.original_image = np.array(pil_image)
        self.processed_image = None
        
        # Set image in zoom controller (this will handle display)
        if self.zoom_controller:
            self.zoom_controller.set_image(pil_image)
        
        # Update pixel inspector with new image
        if self.pixel_inspector:
            self.pixel_inspector.set_image(self.original_image)
        
        # Update UI state
        self._update_ui_state()
        
        # Update status bar with image info
        if self.status_bar:
            self.status_bar.set_image_info(
                pil_image.width, pil_image.height, filename
            )
    
    def _select_colorspace(self, colorspace_name):
        """Select a colorspace."""
        self.current_colorspace = colorspace_name
        self._highlight_colorspace_button(colorspace_name)
        self.status_bar.set_main_status(f"Selected colorspace: {colorspace_name}")
    
    def _highlight_colorspace_button(self, colorspace_name):
        """Highlight the selected colorspace button."""
        # Reset all buttons to normal style
        for btn in self.colorspace_buttons.values():
            btn.configure(style='TButton')
        
        # Highlight selected button using a different approach for ttk
        if colorspace_name in self.colorspace_buttons:
            # Create a custom style for the selected button
            style = ttk.Style()
            style.configure('Selected.TButton', background='lightblue')
            self.colorspace_buttons[colorspace_name].configure(style='Selected.TButton')
    
    def _on_scale_change(self, value):
        """Handle scale slider change."""
        self.current_scale = float(value)
        self.scale_label.configure(text=f"{int(self.current_scale)}")
    
    def _process_image(self):
        """Process the current image with selected parameters."""
        if self.original_image is None:
            messagebox.showerror("Error", "No image loaded")
            return
        
        # Disable UI during processing
        self.process_button.configure(state=tk.DISABLED)
        self.status_bar.set_main_status("Processing...")
        self.status_bar.show_progress(0)
        self.root.update()
        
        # Process in separate thread to keep UI responsive
        def process_thread():
            try:
                # Make a copy to avoid modifying original
                processing_image = self.original_image.copy()
                
                # Apply auto contrast if requested (before decorrelation stretch)
                if self.auto_contrast_var.get():
                    processing_image = self.dstretch.apply_auto_contrast(
                        processing_image,
                        clip_percentage=self.contrast_clip_var.get(),
                        preserve_colors=self.preserve_colors_var.get()
                    )
                
                # Apply decorrelation stretch
                result = self.dstretch.process(
                    processing_image,
                    colorspace=self.current_colorspace,
                    scale=self.current_scale
                )
                
                # Store processed image
                self.processed_image = result.processed_image
                
                # Apply inversion if requested
                if self.invert_var.get():
                    self.processed_image = self.dstretch.apply_invert(
                        self.processed_image,
                        invert_mode=self.invert_mode_var.get()
                    )
                
                # Update UI on main thread
                self.root.after(0, self._on_processing_complete, True)
                
            except Exception as e:
                self.root.after(0, self._on_processing_complete, False, str(e))
        
        threading.Thread(target=process_thread, daemon=True).start()
    
    def _on_processing_complete(self, success, error_message=None):
        """Handle processing completion."""
        # Re-enable UI
        self.process_button.configure(state=tk.NORMAL)
        self.status_bar.hide_progress()
        
        if success:
            # Convert processed image to PIL and display via zoom controller
            pil_image = Image.fromarray(self.processed_image)
            if self.zoom_controller:
                self.zoom_controller.set_image(pil_image)
            
            # Update pixel inspector with processed image
            if self.pixel_inspector:
                self.pixel_inspector.set_image(self.processed_image)
            
            # Update status bar with processing info
            self.status_bar.set_main_status(f"Processed with {self.current_colorspace}, scale {int(self.current_scale)}")
            self.status_bar.set_processing_info(self.current_colorspace, self.current_scale)
            self.reset_button.configure(state=tk.NORMAL)
        else:
            self.infrastructure.error_manager.handle_error(
                Exception(error_message), "Image Processing", error_message
            )
            self.status_bar.set_main_status("Processing failed")
    
    def _reset_to_original(self):
        """Reset to original image."""
        if self.original_image is not None:
            pil_image = Image.fromarray(self.original_image)
            if self.zoom_controller:
                self.zoom_controller.set_image(pil_image)
            self.processed_image = None
            
            # Update pixel inspector with original image
            if self.pixel_inspector:
                self.pixel_inspector.set_image(self.original_image)
            
            self.status_bar.set_main_status("Reset to original image")
            self.status_bar.set_processing_info()  # Clear processing info
            self.reset_button.configure(state=tk.DISABLED)
    
    def _save_image(self):
        """Save the current image."""
        current_image = self.processed_image if self.processed_image is not None else self.original_image
        
        if current_image is None:
            messagebox.showerror("Error", "No image to save")
            return
        
        file_types = [
            ('JPEG files', '*.jpg'),
            ('PNG files', '*.png'),
            ('TIFF files', '*.tiff'),
            ('All files', '*.*')
        ]
        
        filename = filedialog.asksaveasfilename(
            title="Save Image",
            filetypes=file_types,
            defaultextension='.jpg'
        )
        
        if filename:
            try:
                pil_image = Image.fromarray(current_image)
                pil_image.save(filename)
                self.status_bar.set_main_status(f"Saved: {Path(filename).name}")
            except Exception as e:
                self.infrastructure.error_manager.handle_error(
                    e, "Save Image", f"Could not save image:\n{e}"
                )
    
    def _show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About DStretch Python",
            "DStretch Python v0.1.0\n\n"
            "Python implementation of the DStretch decorrelation stretch algorithm\n"
            "for enhancing archaeological rock art images.\n\n"
            "Based on the original DStretch ImageJ plugin by Jon Harman."
        )
    
    def _update_ui_state(self):
        """Update UI state based on current conditions."""
        has_image = self.original_image is not None
        has_processed = self.processed_image is not None
        
        # Enable/disable buttons
        self.process_button.configure(state=tk.NORMAL if has_image else tk.DISABLED)
        self.reset_button.configure(state=tk.NORMAL if has_processed else tk.DISABLED)
    
    def run(self):
        """Start the GUI application."""
        self.root.mainloop()


def main():
    """Main entry point for GUI application."""
    app = DStretchGUI()
    app.run()


if __name__ == '__main__':
    main()