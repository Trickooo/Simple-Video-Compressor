import ffmpeg
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re
import time
import os
import tkinter.font as font


class TrickCompressor:
    def __init__(self, root):
        self.root = root
        self.root.title("Trickooo Video Compressor")

        try:
            self.root.iconbitmap('d:\pyprog\comp.ico')
        except tk.TclError:
            print("Icon ERROR.")

        self.input_path = None
        self.output_path = None
        self.total_duration = 0

        style = ttk.Style()
        style.theme_use('default')
        style.configure("Striped.blue.Horizontal.TProgressbar",
                        troughcolor='white',
                        background='blue',
                        thickness=20)

        default_font = font.Font(family="Century Gothic", size=9, weight="bold")
        self.select_input_btn = tk.Button(root, text="Input Video", font=default_font, command=self.select_input_file)
        self.select_input_btn.pack(pady=10)

        self.select_output_btn = tk.Button(root, text="Output Location/Name", font=default_font, command=self.select_output_file)
        self.select_output_btn.pack(pady=10)

        # Progress Bar
        self.progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate", style="Striped.blue.Horizontal.TProgressbar")
        self.progress.pack(pady=20, padx=20)

        self.label = tk.Label(root, text="Waiting for file...", font=default_font)
        self.label.pack()

        self.eta_label = tk.Label(root, text="")
        self.eta_label.pack()

        self.start_button = tk.Button(root, text="Start Compression", font=default_font, command=self.start_compression, state=tk.DISABLED)
        self.start_button.pack(pady=10)

    def select_input_file(self):
        path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.mkv *.avi *.mov")])
        if path:
            self.input_path = path
            self.label.config(text=f"Video Input: {os.path.basename(path)}")
            self.check_ready_to_start()

    def select_output_file(self):
        path = filedialog.asksaveasfilename(defaultextension=".mp4",
                                            filetypes=[("MP4 file", "*.mp4")],
                                            title="Save Video as...")
        if path:
            self.output_path = path
            self.label.config(text=f"Output: {os.path.basename(path)}")
            self.check_ready_to_start()

    def check_ready_to_start(self):
        if self.input_path and self.output_path:
            self.total_duration = self.get_video_duration(self.input_path)
            if self.total_duration > 0:
                self.start_button.config(state=tk.NORMAL)
            else:
                messagebox.showerror("Error", "Could not determine video duration.")

    def get_video_duration(self, filepath):
        try:
            probe = ffmpeg.probe(filepath)
            return float(probe['format']['duration'])
        except Exception as e:
            print("Error getting duration:", e)
            return 0

    def start_compression(self):
        self.start_button.config(state=tk.DISABLED)
        threading.Thread(target=self.compress_video).start()

    def hms_to_sec(self, h, m, s):
        return int(h) * 3600 + int(m) * 60 + float(s)

    def compress_video(self):
        cmd = (
            ffmpeg
            .input(self.input_path)
            .output(self.output_path, 
                    vcodec='libx264',
                    crf=28, 
                    preset='medium')
            .compile()
        )

        start_time = time.time()

        creationflags = 0
        if os.name == 'nt':
            creationflags = subprocess.CREATE_NO_WINDOW
        
        process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True, creationflags=creationflags)

        frame_re = re.compile(r'time=(\d{1,2}):(\d{1,2}):(\d{1,2}\.\d{1,2})')

        for line in process.stderr:
            line = line.strip()
            match = frame_re.search(line)
            if match:
                try:
                    h, m, s = match.groups()
                    current_time = self.hms_to_sec(h, m, s)
                    percent = (current_time / self.total_duration) * 100
                    elapsed = time.time() - start_time
                    remaining = (elapsed / percent) * (100 - percent) if percent > 0 else 0
                    self.progress["value"] = percent
                    self.label.config(text=f"Progress: {percent:.2f}%")
                    self.eta_label.config(text=f"ETA: {int(remaining)}s")
                    self.root.update_idletasks()
                except (ValueError, ZeroDivisionError) as e:
                    print(f"Error calculating ETA: {e}")
                    continue

        self.progress["value"] = 100
        self.label.config(text="Video compression completed!")
        self.eta_label.config(text="")
        messagebox.showinfo("Success!", "Video compression completed!")


if __name__ == "__main__":
    root = tk.Tk()
    app = TrickCompressor(root)
    root.resizable(False, False)
    root.mainloop()
