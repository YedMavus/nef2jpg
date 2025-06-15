import rawpy
import imageio
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image
import os
import io

class NEFConverterApp:
    def __init__(self, master):
        self.master = master
        master.title("NEF to JPG Converter")

        self.frame = ttk.Frame(master, padding=20)
        self.frame.grid()

        self.nef_files = []
        self.dest_folder = ""
        self.estimate_image = None
        self.cancel_requested = False
        self.original_pixel_count = 0

        # JPEG Quality slider
        ttk.Label(self.frame, text="JPEG Compression Quality:").grid(column=0, row=0, sticky="w")
        self.quality_slider = tk.Scale(self.frame, from_=1, to=100, orient=tk.HORIZONTAL, command=self.update_estimated_size)
        self.quality_slider.set(90)
        self.quality_slider.grid(column=1, row=0, sticky="ew")

        # Estimated size label
        self.size_label = ttk.Label(self.frame, text="Estimated size: N/A")
        self.size_label.grid(column=0, row=1, columnspan=2, sticky="w")

        # File and folder selectors
        ttk.Button(self.frame, text="Select NEF Files", command=self.select_files).grid(column=0, row=2, columnspan=2, pady=5, sticky="ew")
        ttk.Button(self.frame, text="Select Destination Folder", command=self.select_folder).grid(column=0, row=3, columnspan=2, pady=5, sticky="ew")

        # Progress bar
        self.progress = ttk.Progressbar(self.frame, length=300, mode='determinate')
        self.progress.grid(column=0, row=4, columnspan=2, pady=10)

        # Convert / Cancel button
        self.convert_button = ttk.Button(self.frame, text="Convert to JPG", command=self.toggle_conversion)
        self.convert_button.grid(column=0, row=5, columnspan=2, pady=10, sticky="ew")

    def select_files(self):
        files = filedialog.askopenfilenames(filetypes=[("NEF files", "*.nef")])
        if files:
            self.nef_files = list(files)
            self.load_preview_image()
            self.update_estimated_size(None)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.dest_folder = folder

    def load_preview_image(self):
        try:
            with rawpy.imread(self.nef_files[0]) as raw:
                rgb = raw.postprocess()
            self.estimate_image = Image.fromarray(rgb).resize((400, 400))
            self.original_pixel_count = rgb.shape[0] * rgb.shape[1]
        except Exception:
            self.estimate_image = None
            self.size_label.config(text="Size estimate: Failed to load preview.")

    def update_estimated_size(self, _):
        if not self.estimate_image:
            self.size_label.config(text="Estimated size: N/A")
            return
        try:
            buffer = io.BytesIO()
            quality = self.quality_slider.get()
            self.estimate_image.save(buffer, format='JPEG', quality=quality)
            preview_size_kb = buffer.tell() / 1024

            scale_factor = self.original_pixel_count / (400 * 400)
            estimated_final_kb = preview_size_kb * scale_factor

            self.size_label.config(text=f"Estimated size: ~{estimated_final_kb:.1f} KB")
        except Exception:
            self.size_label.config(text="Size estimate: Failed")

    def toggle_conversion(self):
        if self.convert_button['text'] == "Cancel":
            self.cancel_requested = True
            self.convert_button.config(state="disabled", text="Cancelling...")
        else:
            self.start_conversion()

    def start_conversion(self):
        if not self.nef_files:
            messagebox.showwarning("No Files", "Please select NEF files to convert.")
            return
        if not self.dest_folder:
            messagebox.showwarning("No Folder", "Please select a destination folder.")
            return

        self.cancel_requested = False
        self.convert_button.config(text="Cancel")

        quality = self.quality_slider.get()
        total = len(self.nef_files)
        self.progress["maximum"] = total
        self.progress["value"] = 0

        success_count = 0
        for idx, file_path in enumerate(self.nef_files):
            if self.cancel_requested:
                break
            try:
                with rawpy.imread(file_path) as raw:
                    rgb = raw.postprocess()
                filename = os.path.splitext(os.path.basename(file_path))[0]
                out_path = os.path.join(self.dest_folder, f"{filename}_Q{quality}.jpg")
                imageio.imwrite(out_path, rgb, quality=quality)
                success_count += 1
            except Exception as e:
                print(f"Error converting {file_path}: {e}")
            self.progress["value"] = idx + 1
            self.master.update_idletasks()

        if self.cancel_requested:
            messagebox.showinfo("Cancelled", f"Conversion cancelled after {success_count} of {total} file(s).")
        else:
            messagebox.showinfo("Conversion Complete", f"Successfully converted {success_count} of {total} file(s).")

        self.convert_button.config(text="Convert to JPG", state="normal")
        self.cancel_requested = False

# Run the GUI
root = tk.Tk()
app = NEFConverterApp(root)
root.mainloop()
