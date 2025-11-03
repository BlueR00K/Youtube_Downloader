import os
import re
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
from datetime import datetime
import yt_dlp


class YoutubeDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader (Legacy)")
        self.root.geometry("800x600")

        # Initialize variables
        self.download_path = os.path.expanduser("~/Downloads")
        self.current_downloads = []
        self.is_downloading = False

        self.setup_ui()

    def setup_ui(self):
        # URL Input
        url_frame = ttk.LabelFrame(
            self.root, text="YouTube URLs", padding="5 5 5 5")
        url_frame.pack(fill="x", padx=10, pady=5)

        self.url_text = scrolledtext.ScrolledText(url_frame, height=5)
        self.url_text.pack(fill="x", padx=5, pady=5)
        ttk.Label(
            url_frame, text="Paste one or more YouTube URLs (one per line)").pack()

        # Options Frame
        options_frame = ttk.LabelFrame(
            self.root, text="Download Options", padding="5 5 5 5")
        options_frame.pack(fill="x", padx=10, pady=5)

        # Quality Selection
        quality_frame = ttk.Frame(options_frame)
        quality_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(quality_frame, text="Quality:").pack(side="left")
        self.quality_var = tk.StringVar(value="1080p")
        quality_menu = ttk.OptionMenu(
            quality_frame,
            self.quality_var,
            "1080p",
            "4K", "1080p", "720p", "480p", "360p",
            "Audio Only (Best)", "Audio Only (MP3)"
        )
        quality_menu.pack(side="left", padx=5)

        # Filename Options
        self.clean_names_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Clean filenames (remove special characters)",
            variable=self.clean_names_var
        ).pack(padx=5, pady=2)

        self.number_files_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Number files in batch downloads",
            variable=self.number_files_var
        ).pack(padx=5, pady=2)

        # Folder Selection
        folder_frame = ttk.Frame(options_frame)
        folder_frame.pack(fill="x", padx=5, pady=5)
        self.folder_label = ttk.Label(
            folder_frame, text=f"Save to: {self.download_path}")
        self.folder_label.pack(side="left", fill="x", expand=True)
        ttk.Button(
            folder_frame,
            text="Change Folder",
            command=self.choose_folder
        ).pack(side="right")

        # Progress Area
        progress_frame = ttk.LabelFrame(
            self.root, text="Download Progress", padding="5 5 5 5")
        progress_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.progress_text = scrolledtext.ScrolledText(
            progress_frame, height=10)
        self.progress_text.pack(fill="both", expand=True, padx=5, pady=5)

        self.progress_bar = ttk.Progressbar(
            progress_frame,
            orient="horizontal",
            mode="determinate"
        )
        self.progress_bar.pack(fill="x", padx=5, pady=5)

        self.status_label = ttk.Label(progress_frame, text="Ready")
        self.status_label.pack(pady=2)

        # Download Button
        self.download_btn = ttk.Button(
            self.root,
            text="Start Download",
            command=self.start_download
        )
        self.download_btn.pack(pady=10)

    def extract_links(self):
        text = self.url_text.get("1.0", "end").strip()
        pattern = r'https?://(?:www\.)?(?:youtu\.be/\S+|youtube\.com/\S+)'
        return re.findall(pattern, text)

    def choose_folder(self):
        folder = filedialog.askdirectory(
            title="Select Download Folder",
            initialdir=self.download_path
        )
        if folder:
            self.download_path = folder
            self.folder_label.config(text=f"Save to: {folder}")

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.progress_text.insert("end", f"[{timestamp}] {message}\n")
        self.progress_text.see("end")
        self.progress_text.update()

    def update_progress(self, d):
        if d['status'] == 'downloading':
            try:
                # Calculate progress percentage
                total = d.get('total_bytes') or d.get(
                    'total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    percentage = (downloaded / total) * 100
                    self.progress_bar["value"] = percentage

                # Update status with speed and ETA
                speed = d.get('speed', 0)
                eta = d.get('eta', 0)
                if speed and eta:
                    speed_mb = speed / 1024 / 1024  # Convert to MB/s
                    status = f"Downloading: {percentage:.1f}% ({speed_mb:.1f} MB/s, ETA: {eta} seconds)"
                    self.status_label.config(text=status)

                self.root.update_idletasks()
            except Exception as e:
                self.log(f"Progress update error: {str(e)}")

    def get_format(self):
        quality = self.quality_var.get()
        if quality == "4K":
            return "bestvideo[height<=2160]+bestaudio/best[height<=2160]"
        elif quality == "1080p":
            return "bestvideo[height<=1080]+bestaudio/best[height<=1080]"
        elif quality == "720p":
            return "bestvideo[height<=720]+bestaudio/best[height<=720]"
        elif quality == "480p":
            return "bestvideo[height<=480]+bestaudio/best[height<=480]"
        elif quality == "360p":
            return "bestvideo[height<=360]+bestaudio/best[height<=360]"
        elif quality == "Audio Only (Best)":
            return "bestaudio/best"
        elif quality == "Audio Only (MP3)":
            return "bestaudio/best"
        return "best"

    def clean_filename(self, filename):
        if not self.clean_names_var.get():
            return filename

        # Remove invalid characters and clean up the filename
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = re.sub(r'\s+', '_', filename.strip())
        return filename

    def download_videos(self, urls):
        if not urls:
            messagebox.showerror("Error", "No valid YouTube URLs found")
            return

        self.log(
            f"Starting download of {len(urls)} videos to {self.download_path}")
        self.download_btn.state(['disabled'])
        self.is_downloading = True

        # Prepare yt-dlp options
        ydl_opts = {
            'format': self.get_format(),
            'outtmpl': os.path.join(
                self.download_path,
                '%(title)s.%(ext)s'
            ),
            'progress_hooks': [self.update_progress],
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
        }

        if self.quality_var.get() == "Audio Only (MP3)":
            ydl_opts.update({
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            })

        def download_thread():
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    for i, url in enumerate(urls, 1):
                        try:
                            # Reset progress for each video
                            self.progress_bar["value"] = 0
                            self.status_label.config(
                                text=f"Downloading video {i} of {len(urls)}")

                            # Get video info first
                            self.log(f"Fetching info for video {i}...")
                            info = ydl.extract_info(url, download=False)
                            title = info.get('title', 'Unknown Title')
                            self.log(f"Downloading: {title}")

                            # Download the video
                            ydl.download([url])
                            self.log(f"✅ Successfully downloaded: {title}")

                        except Exception as e:
                            self.log(f"❌ Error downloading {url}: {str(e)}")
                            continue

                self.log("All downloads completed!")

            except Exception as e:
                self.log(f"Fatal error: {str(e)}")

            finally:
                self.is_downloading = False
                self.download_btn.state(['!disabled'])
                self.status_label.config(text="Ready")
                self.progress_bar["value"] = 0
                self.root.update_idletasks()

        def download_thread():
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    for i, url in enumerate(urls, 1):
                        try:
                            # Reset progress for each video
                            self.progress_bar["value"] = 0
                            self.status_label.config(
                                text=f"Downloading video {i} of {len(urls)}")

                            # Get video info first
                            self.log(f"Fetching info for video {i}...")
                            info = ydl.extract_info(url, download=False)
                            title = info.get('title', 'Unknown Title')
                            self.log(f"Downloading: {title}")

                            # Download the video
                            ydl.download([url])
                            self.log(f"✅ Successfully downloaded: {title}")

                        except Exception as e:
                            self.log(f"❌ Error downloading {url}: {str(e)}")
                            continue

                self.log("All downloads completed!")

            except Exception as e:
                self.log(f"Fatal error: {str(e)}")

            finally:
                self.is_downloading = False
                self.download_btn.state(['!disabled'])
                self.status_label.config(text="Ready")
                self.progress_bar["value"] = 0
                self.root.update_idletasks()

        threading.Thread(target=download_thread, daemon=True).start()

    def start_download(self):
        if self.is_downloading:
            return

        urls = self.extract_links()
        if not urls:
            messagebox.showerror("Error", "No YouTube URLs found in the input")
            return

        if not os.path.isdir(self.download_path):
            messagebox.showerror(
                "Error", "Please select a valid download folder")
            return

        self.progress_text.delete("1.0", "end")
        self.download_videos(urls)


def main():
    root = tk.Tk()
    app = YoutubeDownloader(root)

    # Set a custom style
    style = ttk.Style()
    style.theme_use('clam')  # or 'alt', 'default', 'classic'

    root.mainloop()


if __name__ == "__main__":
    main()
