import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import threading
import re
import datetime
import queue  # Import the queue module
import time
import shutil

class App:
    def __init__(self, root):
        # Initialize queues first, before any other operations
        self.log_queue = queue.Queue()
        self.progress_queue = queue.Queue()
        
        self.root = root
        self.root.title("MKV to MP4 Converter")

        # Add detailed startup logging
        self.log("=== Application Startup ===")
        self.log(f"Python Version: {sys.version}")
        self.log(f"Running Mode: {'Frozen/Installed' if getattr(sys, 'frozen', False) else 'Development'}")
        self.log(f"Application Path: {sys.executable}")
        self.log(f"Working Directory: {os.getcwd()}")
        
        # Log installation directory contents
        install_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()
        self.log(f"Installation Directory: {install_dir}")
        try:
            self.log("Directory contents:")
            for item in os.listdir(install_dir):
                item_path = os.path.join(install_dir, item)
                self.log(f"- {item} ({'Directory' if os.path.isdir(item_path) else 'File'})")
        except Exception as e:
            self.log(f"Error listing directory: {str(e)}")
        
        self.log("=========================")

        self.root.geometry("500x400")

        # Set the window icon
        icon_path = self.resource_path("icon.ico")
        try:
            self.root.iconbitmap(icon_path)
        except tk.TclError:
            print(f"Warning: Could not load icon from {icon_path}")

        # Create a frame for buttons
        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(pady=20)

        self.select_button = tk.Button(self.button_frame, text="Select MKV File", command=self.select_file)
        self.select_button.pack(side=tk.LEFT, padx=5)

        self.run_button = tk.Button(self.button_frame, text="Run Conversion", command=self.start_conversion, state=tk.DISABLED)
        self.run_button.pack(side=tk.LEFT, padx=5)

        # Add a label to show selected file
        self.file_label = tk.Label(self.root, text="No file selected", wraplength=450)
        self.file_label.pack(pady=5)

        self.progress = ttk.Progressbar(self.root, orient="horizontal", mode="determinate", length=400)
        self.progress.pack(pady=10)

        self.progress_label = tk.Label(self.root, text="0%", anchor="center")
        self.progress_label.pack()

        self.log_text = tk.Text(self.root, height=10, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.total_duration = 0
        self.current_time = 0

        # Add selected_file attribute
        self.selected_file = None

        # Add a label for estimated time
        self.eta_label = tk.Label(self.root, text="", anchor="center")
        self.eta_label.pack()
        
        # Add start_time attribute
        self.start_time = None

        # Start a periodic task to check the queues
        self.root.after(100, self.process_queue)

    def process_queue(self):
        """Process items in the queues and update the GUI."""
        try:
            while True:
                # Update logs
                message = self.log_queue.get_nowait()
                self.update_log(message)
        except queue.Empty:
            pass

        try:
            while True:
                # Update progress
                percentage = self.progress_queue.get_nowait()
                self.update_progress(percentage)
        except queue.Empty:
            pass

        # Schedule the next queue check
        self.root.after(100, self.process_queue)

    def update_log(self, message):
        """Update the log text widget in the GUI thread."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)  # Scroll to the bottom

    def update_progress(self, percentage):
        """Update the progress bar and ETA in the GUI thread."""
        # Round to 1 decimal place for progress bar
        rounded_percentage = round(percentage, 1)
        self.progress["value"] = rounded_percentage
        self.progress_label.config(text=f"{rounded_percentage:.1f}%")
        
        # Calculate and display ETA
        if self.start_time and percentage > 0:
            elapsed_time = time.time() - self.start_time
            estimated_total_time = elapsed_time / (percentage / 100)
            remaining_time = estimated_total_time - elapsed_time
            
            # Format remaining time
            if remaining_time > 3600:
                eta_text = f"Estimated time remaining: {remaining_time/3600:.1f} hours"
            elif remaining_time > 60:
                eta_text = f"Estimated time remaining: {remaining_time/60:.1f} minutes"
            else:
                eta_text = f"Estimated time remaining: {remaining_time:.0f} seconds"
                
            self.eta_label.config(text=eta_text)

    def log(self, message):
        """Safe logging method"""
        try:
            if hasattr(self, 'log_queue'):
                self.log_queue.put(message)
            if hasattr(self, 'log_text'):
                self.root.after(0, self.update_log, message)
        except Exception as e:
            print(f"Logging error: {str(e)}")
            print(f"Failed to log message: {message}")

    def update_progress_in_thread(self, percentage):
        """Put a progress update into the queue."""
        self.progress_queue.put(percentage)

    def resource_path(self, relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller."""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def get_ffmpeg_path(self):
        """Get the path to FFmpeg executables."""
        # If frozen (onefile or onedir), check extraction path or exe directory
        if getattr(sys, 'frozen', False):
            # Determine base path (use _MEIPASS for onefile or exe directory for onedir)
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
            self.log(f"Base path: {base_path}")
            # Look for FFmpeg executables alongside the base path
            ffmpeg_path = os.path.join(base_path, 'ffmpeg.exe')
            ffprobe_path = os.path.join(base_path, 'ffprobe.exe')
            self.log(f"Looking for FFmpeg at: {ffmpeg_path}")
            if os.path.exists(ffmpeg_path) and os.path.exists(ffprobe_path):
                self.log(f"Found FFmpeg at: {ffmpeg_path}")
                return ffmpeg_path, ffprobe_path
            # Fallback to system PATH if not found
            self.log("FFmpeg not found beside executable, searching in system PATH")
            ffmpeg_path_system = shutil.which('ffmpeg')
            ffprobe_path_system = shutil.which('ffprobe')
            if ffmpeg_path_system and ffprobe_path_system:
                self.log(f"Found FFmpeg in PATH at: {ffmpeg_path_system}")
                return ffmpeg_path_system, ffprobe_path_system
            raise FileNotFoundError("FFmpeg not found. Please ensure the application was installed correctly.")
        else:
            # Development environment
            self.log("Running in development environment")
            base_path = os.path.dirname(os.path.abspath(__file__))
            ffmpeg_path = os.path.join(base_path, 'ffmpeg', 'ffmpeg.exe')
            ffprobe_path = os.path.join(base_path, 'ffmpeg', 'ffprobe.exe')
            return ffmpeg_path, ffprobe_path

    def get_video_duration(self, input_file):
        """Get video duration using ffmpeg."""
        try:
            ffmpeg_path, _ = self.get_ffmpeg_path()
            
            # Add startupinfo to hide console window
            startupinfo = None
            if os.name == 'nt':  # Windows
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            # Use full path to ffmpeg executable
            command = [
                ffmpeg_path,  # Use full path
                '-i', input_file
            ]
            
            self.log(f"Running duration command: {' '.join(command)}")
            
            # Create process and capture output
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                startupinfo=startupinfo
            )
            
            # Read output
            stdout, stderr = process.communicate()
            output = stdout + stderr
            
            # Look for duration in ffmpeg output
            duration_match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})', output)
            if duration_match:
                hours = int(duration_match.group(1))
                minutes = int(duration_match.group(2))
                seconds = int(duration_match.group(3))
                centiseconds = int(duration_match.group(4))
                
                total_seconds = hours * 3600 + minutes * 60 + seconds + centiseconds / 100
                self.log(f"Video duration: {total_seconds:.3f} seconds")
                return total_seconds
                
            self.log("Could not find duration in FFmpeg output")
            self.log(f"FFmpeg output: {output}")
            return 0
                
        except Exception as e:
            self.log(f"Error getting duration: {str(e)}")
            self.log(f"Exception type: {type(e)}")
            import traceback
            self.log(f"Traceback: {traceback.format_exc()}")
            return 0

    def convert_to_mp4(self, mkv_file, output_folder):
        try:
            ffmpeg_path, _ = self.get_ffmpeg_path()
            self.log(f"Using FFmpeg at: {ffmpeg_path}")

            # Windows-specific process configuration
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            # Format output path
            name, _ = os.path.splitext(os.path.basename(mkv_file))
            out_name = os.path.join(output_folder, name + ".mp4")
            
            # Format paths for Windows
            mkv_file = mkv_file.replace('/', '\\')
            out_name = out_name.replace('/', '\\')

            # Optimized FFmpeg command for better compression
            convert_command = [
                ffmpeg_path,
                '-i', mkv_file,
                '-c:v', 'libx264',
                '-preset', 'slow',  # Slower preset = better compression
                '-crf', '23',      # Constant Rate Factor (18-28 is good, higher = smaller file)
                '-c:a', 'aac',
                '-b:a', '128k',    # Reduced audio bitrate
                '-movflags', '+faststart',  # Optimize for web playback
                '-y',
                out_name
            ]

            self.log(f"Starting conversion with optimized settings...")
            
            # Add start time tracking
            start_time = time.time()
            
            # Create the process with working directory set
            process = subprocess.Popen(
                convert_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1,
                encoding='utf-8',
                errors='replace',
                startupinfo=startupinfo
            )

            last_percentage = -1  # Track last percentage for logging
            last_progress_update = -1  # Track last progress bar update
            
            while True:
                line = process.stderr.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    # Log FFmpeg output with exact percentage (0.01% increments)
                    if "time=" in line:
                        try:
                            time_match = re.search(r'time=(\d+:\d+:\d+\.\d+)', line)
                            if time_match:
                                time_str = time_match.group(1)
                                h, m, s = map(float, time_str.replace('.', ':').split(':')[:-1])
                                current_time = h * 3600 + m * 60 + s
                                
                                if self.total_duration > 0:
                                    # Calculate exact percentage
                                    exact_percentage = (current_time / self.total_duration) * 100
                                    
                                    # Log if percentage changed by at least 0.01%
                                    rounded_log_percentage = round(exact_percentage, 2)
                                    if rounded_log_percentage != last_percentage:
                                        self.log(f"Progress: {rounded_log_percentage:.2f}%")
                                        last_percentage = rounded_log_percentage
                                    
                                    # Update progress bar if changed by at least 0.1%
                                    rounded_progress = round(exact_percentage, 1)
                                    if rounded_progress != last_progress_update:
                                        self.update_progress_in_thread(exact_percentage)
                                        last_progress_update = rounded_progress
                                        
                                        # Update ETA with each progress bar update
                                        if self.start_time:
                                            elapsed_time = time.time() - self.start_time
                                            if exact_percentage > 0:
                                                total_estimated_time = elapsed_time / (exact_percentage / 100)
                                                remaining_time = total_estimated_time - elapsed_time
                                                self.update_eta_in_thread(remaining_time)
                        except Exception as e:
                            self.log(f"Error parsing progress: {str(e)}")
                            continue
                    else:
                        # Log other FFmpeg output
                        self.log(f"FFmpeg: {line.strip()}")

            # Get the final output
            stdout, stderr = process.communicate()
            
            if stdout:
                self.log(f"Final stdout: {stdout}")
            if stderr:
                self.log(f"Final stderr: {stderr}")

            if process.returncode == 0:
                final_size = os.path.getsize(out_name) / (1024 * 1024)
                elapsed_time = time.time() - start_time
                self.log(f"Conversion completed in {elapsed_time:.1f} seconds")
                self.log(f"Final file size: {final_size:.2f} MB")
                self.log("Conversion completed successfully!")
                messagebox.showinfo("Success", "Conversion completed successfully!")
            else:
                raise Exception(f"FFmpeg process returned non-zero exit code: {process.returncode}\nStderr: {stderr}")

        except Exception as e:
            self.log(f"Error during conversion: {str(e)}")
            self.log(f"Exception type: {type(e)}")
            self.log(f"Exception details: {str(e)}")
            messagebox.showerror("Error", f"Conversion failed: {str(e)}")
        finally:
            self.update_progress_in_thread(100)

    def select_file(self):
        """Handle file selection."""
        file_path = filedialog.askopenfilename(filetypes=[("MKV files", "*.mkv")])
        if file_path:
            # Reset progress-related elements
            self.progress["value"] = 0
            self.progress_label.config(text="0%")
            self.eta_label.config(text="")
            self.log_text.delete('1.0', tk.END)
            self.total_duration = 0
            self.current_time = 0
            self.start_time = None
            
            # Update file selection
            self.selected_file = file_path
            self.file_label.config(text=f"Selected: {os.path.basename(file_path)}")
            self.run_button.config(state=tk.NORMAL)  # Enable the run button

    def start_conversion(self):
        """Start the conversion process."""
        if self.selected_file:
            self.total_duration = self.get_video_duration(self.selected_file)
            self.log(f"Total duration: {self.total_duration:.3f} seconds")
            output_folder = os.path.dirname(self.selected_file)
            self.progress["value"] = 0
            self.progress_label.config(text="0%")
            self.log_text.delete('1.0', tk.END)
            self.current_time = 0
            
            # Disable buttons during conversion
            self.select_button.config(state=tk.DISABLED)
            self.run_button.config(state=tk.DISABLED)
            
            # Reset and store start time
            self.start_time = time.time()
            self.eta_label.config(text="Calculating remaining time...")
            
            # Start conversion in a separate thread
            threading.Thread(
                target=self.conversion_thread,
                args=(self.selected_file, output_folder),
                daemon=True
            ).start()

    def conversion_thread(self, file_path, output_folder):
        """Wrapper for convert_to_mp4 that re-enables buttons when done."""
        try:
            self.convert_to_mp4(file_path, output_folder)
        finally:
            # Re-enable buttons after conversion (whether successful or not)
            self.root.after(0, self.enable_buttons)

    def enable_buttons(self):
        """Re-enable buttons after conversion is complete."""
        self.select_button.config(state=tk.NORMAL)
        self.run_button.config(state=tk.NORMAL)

    def update_eta_in_thread(self, remaining_seconds):
        """Update the ETA label through the main thread."""
        def update():
            if remaining_seconds > 3600:
                eta_text = f"Estimated time remaining: {remaining_seconds/3600:.1f} hours"
            elif remaining_seconds > 60:
                eta_text = f"Estimated time remaining: {remaining_seconds/60:.1f} minutes"
            else:
                eta_text = f"Estimated time remaining: {remaining_seconds:.0f} seconds"
            self.eta_label.config(text=eta_text)
        
        self.root.after(0, update)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()