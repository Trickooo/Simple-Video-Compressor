import ffmpeg
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re
import time
import os
import tkinter.font as font


class FFmpegCompressorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Patrick's Compressor")

        self.input_path = None  # can be file or folder
        self.output_folder = None
        self.video_files = []
        self.total_duration = 0
        self.batch_mode = False

        style = ttk.Style()
        style.theme_use('default')
        style.configure("Striped.blue.Horizontal.TProgressbar",
                        troughcolor='white',
                        background='blue',
                        thickness=20)

        default_font = font.Font(family="Century Gothic", size=9, weight="bold")

        # Input Button and Label
        self.select_input_btn = tk.Button(root, text="Select Input", font=default_font, command=self.show_input_options)
        self.select_input_btn.pack(pady=(10, 0))
        self.input_display = tk.Label(root, text="No input selected", font=default_font, fg="gray")
        self.input_display.pack(pady=(2, 10))

        # Output Button and Label
        self.select_output_btn = tk.Button(root, text="Select Output Folder", font=default_font, command=self.select_output_folder)
        self.select_output_btn.pack(pady=(0, 0))
        self.output_display = tk.Label(root, text="No output folder selected", font=default_font, fg="gray")
        self.output_display.pack(pady=(2, 10))

        self.progress = ttk.Progressbar(
            root,
            orient="horizontal",
            length=300,
            mode="determinate", 
            style="Striped.blue.Horizontal.TProgressbar"
        )
        self.progress.pack(pady=20, padx=20)

        self.label = tk.Label(root, text="", font=default_font)
        self.label.pack()

        self.eta_label = tk.Label(root, text="")
        self.eta_label.pack()

        self.start_button = tk.Button(
            root,
            text="Start Compression",
            font=default_font,
            command=self.start_compression,
            state=tk.DISABLED
        )
        self.start_button.pack(pady=10)

    def show_input_options(self):
        # Create a popup menu
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Select File", command=self.select_input_file)
        menu.add_command(label="Select Folder", command=self.select_input_folder)
        # Display at mouse position
        menu.tk_popup(self.root.winfo_pointerx(), self.root.winfo_pointery())

    def select_input_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.mkv *.avi *.mov")]
        )
        if file_path:
            self.input_path = file_path
            self.batch_mode = False
            self.video_files = [os.path.basename(file_path)]
            self.input_display.config(text=os.path.basename(file_path), fg="black")
            self.label.config(text="Ready for single compression")
            self.check_ready_to_start()

    def select_input_folder(self):
        folder = filedialog.askdirectory(title="Select Folder for Batch Compression")
        if folder:
            self.input_path = folder
            self.batch_mode = True
            self.video_files = [f for f in os.listdir(folder)
                                if f.lower().endswith(('.mp4', '.mkv', '.avi', '.mov'))]
            if not self.video_files:
                messagebox.showerror("Error", "No video files found in the selected folder.")
                self.input_path = None
                self.input_display.config(text="No input selected", fg="gray")
                return
            self.input_display.config(text=os.path.basename(folder), fg="black")
            self.label.config(text=f"{len(self.video_files)} video(s) ready for batch compression")
            self.check_ready_to_start()

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder = folder
            self.output_display.config(text=os.path.basename(folder), fg="black")
            self.check_ready_to_start() 

    def check_ready_to_start(self):
        if self.input_path and self.output_folder and self.video_files:
            self.start_button.config(state=tk.NORMAL)
        else:
            self.start_button.config(state=tk.DISABLED)

    def get_video_duration(self, filepath):
        try:
            probe = ffmpeg.probe(filepath)
            return float(probe['format']['duration'])
        except Exception as e:
            print("Error getting duration:", e)
            return 0

    def start_compression(self):
        self.start_button.config(state=tk.DISABLED)
        thread = threading.Thread(
            target=self.batch_compress_videos if self.batch_mode else self.compress_single_file
        )
        thread.start()

    def compress_single_file(self):
        filename = self.video_files[0]
        input_path = self.input_path
        output_filename = os.path.splitext(filename)[0] + "_compressed.mp4"
        output_path = os.path.join(self.output_folder, output_filename)
        self.label.config(text=f"Compressing: {filename}")
        self.compress_video(input_path, output_path)
        self.label.config(text="File compressed!")
        self.eta_label.config(text="")
        messagebox.showinfo("Done", "Single video compression completed!")

    def batch_compress_videos(self):
        for index, filename in enumerate(self.video_files, start=1):
            input_path = os.path.join(self.input_path, filename)
            output_filename = os.path.splitext(filename)[0] + "_compressed.mp4"
            output_path = os.path.join(self.output_folder, output_filename)

            self.label.config(text=f"Compressing ({index}/{len(self.video_files)}): {filename}")
            self.compress_video(input_path, output_path)

        self.progress["value"] = 100
        self.label.config(text="All videos compressed!")
        self.eta_label.config(text="")
        messagebox.showinfo("Done", "Batch video compression completed!")

    def compress_video(self, input_path, output_path):
        self.total_duration = self.get_video_duration(input_path)
        if self.total_duration == 0:
            return

        cmd = (
            ffmpeg
            .input(input_path)
            .output(output_path, vcodec='libx264', crf=28, preset='medium')
            .compile()
        )

        start_time = time.time()
        process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True)

        frame_re = re.compile(r'time=(\d{1,2}):(\d{1,2}):(\d{1,2}\.\d{1,2})')

        for line in process.stderr:
            match = frame_re.search(line)
            if match:
                h, m, s = match.groups()
                current_time = int(h) * 3600 + int(m) * 60 + float(s)
                percent = (current_time / self.total_duration) * 100
                elapsed = time.time() - start_time
                remaining = (elapsed / percent) * (100 - percent) if percent > 0 else 0
                self.progress["value"] = percent
                self.eta_label.config(text=f"ETA: {int(remaining)}s")
                self.root.update_idletasks()

        self.progress["value"] = 0


if __name__ == "__main__":
    root = tk.Tk()
    app = FFmpegCompressorApp(root)
    root.resizable(False, False)
    root.mainloop()
