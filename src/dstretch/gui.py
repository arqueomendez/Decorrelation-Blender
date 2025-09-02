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

from . import DecorrelationStretch, get_available_colorspaces


class DStretchGUI:
    """Main GUI application for DStretch."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("DStretch Python")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Application state
        self.dstretch = DecorrelationStretch()
        self.original_image = None
        self.processed_image = None
        self.current_colorspace = "YDS"
        self.current_scale = 15.0
        
        # UI components
        self.image_display = None
        self.colorspace_buttons = {}
        self.scale_var = None
        self.status_var = None
        self.process_button = None
        self.reset_button = None
        
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
        main_frame.rowconfigure(0, weight=1)
        
        # Left panel: Image display
        self._setup_image_panel(main_frame)
        
        # Right panel: Controls
        self._setup_control_panel(main_frame)
        
        # Bottom: Status bar
        self._setup_status_bar()
    
    def _setup_image_panel(self, parent):
        """Setup the image display panel."""
        image_frame = ttk.LabelFrame(parent, text="Image", padding="10")
        image_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        # Configure grid
        image_frame.columnconfigure(0, weight=1)
        image_frame.rowconfigure(0, weight=1)
        
        # Canvas for image display
        self.image_canvas = tk.Canvas(
            image_frame,
            bg='lightgray',
            width=400,
            height=300
        )
        self.image_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbars for large images
        v_scrollbar = ttk.Scrollbar(image_frame, orient=tk.VERTICAL, command=self.image_canvas.yview)
        h_scrollbar = ttk.Scrollbar(image_frame, orient=tk.HORIZONTAL, command=self.image_canvas.xview)
        
        self.image_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Placeholder text
        self.image_canvas.create_text(
            200, 150,
            text="No image loaded\nUse File -> Open Image",
            font=('Arial', 12),
            fill='gray',
            tags='placeholder'
        )
    
    def _setup_control_panel(self, parent):
        """Setup the control panel with colorspace buttons and scale slider."""
        control_frame = ttk.LabelFrame(parent, text="Controls", padding="10")
        control_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
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
        
        # Action buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
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
    
    def _setup_colorspace_buttons(self, parent):
        """Setup the grid of colorspace buttons."""
        available_colorspaces = get_available_colorspaces()
        
        # Organize colorspaces in rows (4 buttons per row to match DStretch layout)
        colorspace_names = list(available_colorspaces.keys())
        rows = []
        for i in range(0, len(colorspace_names), 4):
            rows.append(colorspace_names[i:i+4])
        
        # Create buttons
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
        """Setup the status bar at the bottom."""
        status_frame = ttk.Frame(self.root)
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        status_frame.columnconfigure(0, weight=1)
    
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
                self.status_var.set(f"Loaded: {Path(filename).name}")
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
        
        # Display image
        self._display_image(pil_image)
        
        # Update UI state
        self._update_ui_state()
    
    def _display_image(self, pil_image):
        """Display a PIL image on the canvas."""
        # Calculate display size (fit to canvas while maintaining aspect ratio)
        canvas_width = self.image_canvas.winfo_width()
        canvas_height = self.image_canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            # Canvas not yet sized, use default
            canvas_width, canvas_height = 400, 300
        
        # Calculate scaling to fit image in canvas
        img_width, img_height = pil_image.size
        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        scale = min(scale_x, scale_y, 1.0)  # Don't scale up
        
        if scale < 1.0:
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            display_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        else:
            display_image = pil_image
        
        # Convert to PhotoImage
        self.photo_image = ImageTk.PhotoImage(display_image)
        
        # Clear canvas and display image
        self.image_canvas.delete('all')
        self.image_canvas.create_image(
            canvas_width // 2,
            canvas_height // 2,
            image=self.photo_image,
            anchor=tk.CENTER
        )
        
        # Update scroll region
        self.image_canvas.configure(scrollregion=self.image_canvas.bbox('all'))
    
    def _select_colorspace(self, colorspace_name):
        """Select a colorspace."""
        self.current_colorspace = colorspace_name
        self._highlight_colorspace_button(colorspace_name)
        self.status_var.set(f"Selected colorspace: {colorspace_name}")
    
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
        self.status_var.set("Processing...")
        self.root.update()
        
        # Process in separate thread to keep UI responsive
        def process_thread():
            try:
                result = self.dstretch.process(
                    self.original_image,
                    colorspace=self.current_colorspace,
                    scale=self.current_scale
                )
                
                # Store processed image
                self.processed_image = result.processed_image
                
                # Update UI on main thread
                self.root.after(0, self._on_processing_complete, True)
                
            except Exception as e:
                self.root.after(0, self._on_processing_complete, False, str(e))
        
        threading.Thread(target=process_thread, daemon=True).start()
    
    def _on_processing_complete(self, success, error_message=None):
        """Handle processing completion."""
        # Re-enable UI
        self.process_button.configure(state=tk.NORMAL)
        
        if success:
            # Display processed image
            pil_image = Image.fromarray(self.processed_image)
            self._display_image(pil_image)
            
            self.status_var.set(f"Processed with {self.current_colorspace}, scale {int(self.current_scale)}")
            self.reset_button.configure(state=tk.NORMAL)
        else:
            messagebox.showerror("Processing Error", f"Failed to process image:\n{error_message}")
            self.status_var.set("Processing failed")
    
    def _reset_to_original(self):
        """Reset to original image."""
        if self.original_image is not None:
            pil_image = Image.fromarray(self.original_image)
            self._display_image(pil_image)
            self.processed_image = None
            self.status_var.set("Reset to original image")
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
                self.status_var.set(f"Saved: {Path(filename).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save image:\n{e}")
    
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