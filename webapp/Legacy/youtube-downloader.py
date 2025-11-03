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

        # Set window size and position
        window_width = 800
        window_height = 700  # Increased height

        # Calculate center position
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)

        # Set geometry and constraints
        self.root.geometry(
            f"{window_width}x{window_height}+{center_x}+{center_y}")
        self.root.minsize(700, 600)  # Increased minimum size

        # Configure grid weight
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # Initialize variables
        self.download_path = os.path.expanduser("~/Downloads")
        self.current_downloads = []
        self.is_downloading = False

        # Check for required dependencies
        self.check_dependencies()

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
        # Download Button Frame (for better positioning)
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=20, pady=15)  # Increased padding

        self.download_btn = ttk.Button(
            btn_frame,
            text="⬇️ Start Download",  # Added emoji for better visibility
            command=self.start_download,
            style='Accent.TButton'  # Custom style for visibility
        )
        self.download_btn.pack(fill="x", ipady=5)  # Added internal padding

    def extract_links(self):
        text = self.url_text.get("1.0", "end").strip()
        # More comprehensive pattern to match YouTube URLs
        patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]+)'
        ]

        links = []
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                video_id = match.group(1)
                # Normalize to standard YouTube URL
                links.append(f'https://www.youtube.com/watch?v={video_id}')

        # Remove duplicates while preserving order
        return list(dict.fromkeys(links))

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

        # Format selection patterns
        format_patterns = {
            "4K": "bestvideo[ext=mp4][height<=2160]+bestaudio[ext=m4a]/best[height<=2160]/best",
            "1080p": "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[height<=1080]/best",
            "720p": "bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[height<=720]/best",
            "480p": "bestvideo[ext=mp4][height<=480]+bestaudio[ext=m4a]/best[height<=480]/best",
            "360p": "bestvideo[ext=mp4][height<=360]+bestaudio[ext=m4a]/best[height<=360]/best",
            "Audio Only (Best)": "bestaudio[ext=m4a]/bestaudio/best",
            "Audio Only (MP3)": "bestaudio/best"
        }

        # Get format string or default to best
        format_str = format_patterns.get(quality, "best[ext=mp4]/best")

        self.log(f"Selected format: {format_str}")
        return format_str

    def export_cookies(self):
        """Export cookies from the browser to a file."""
        try:
            # Create a temporary YoutubeDL instance
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                # Try to get cookies from browsers
                for browser in ['chrome', 'firefox', 'edge', 'opera', 'brave', 'chromium']:
                    try:
                        cookie_jar = ydl.cookiejar.get_cookies_from_browser(
                            browser)
                        if cookie_jar:
                            # Convert cookies to Netscape format
                            with open(self.cookies_file, 'w', encoding='utf-8') as f:
                                for cookie in cookie_jar:
                                    f.write(f"{cookie.domain}\tTRUE\t{cookie.path}\t"
                                            f"{'TRUE' if cookie.secure else 'FALSE'}\t{cookie.expires}\t"
                                            f"{cookie.name}\t{cookie.value}\n")
                            self.log(
                                f"Successfully exported cookies from {browser}")
                            return True
                    except Exception as e:
                        continue

                self.log("Could not export cookies from any browser")
                return False
        except Exception as e:
            self.log(f"Error exporting cookies: {str(e)}")
            return False

    def check_dependencies(self):
        """Check if required dependencies are installed."""
        try:
            import yt_dlp
        except ImportError:
            messagebox.showerror(
                "Error",
                "yt-dlp is not installed. Please run: pip install yt-dlp"
            )
            sys.exit(1)

        # Check for ffmpeg (needed for audio conversion)
        if sys.platform == 'win32':
            ffmpeg_cmd = 'where ffmpeg'
        else:
            ffmpeg_cmd = 'which ffmpeg'

        if os.system(ffmpeg_cmd) != 0:
            messagebox.showwarning(
                "Warning",
                "ffmpeg is not found. Audio conversion may not work properly.\n"
                "Please install ffmpeg to enable all features."
            )

    def clean_filename(self, filename, index=None):
        if not filename:
            return "download"

        # First clean the filename if option is enabled
        if self.clean_names_var.get():
            # Remove invalid characters
            filename = re.sub(r'[<>:"/\\|?*]', '', filename)
            # Replace spaces and multiple dots
            filename = re.sub(r'\s+', '_', filename.strip())
            filename = re.sub(r'\.+', '.', filename)
            # Remove non-ASCII characters
            filename = ''.join(c for c in filename if ord(c) < 128)

        # Add numbering if enabled and index is provided
        if self.number_files_var.get() and index is not None:
            name, ext = os.path.splitext(filename)
            filename = f"{index:03d}_{name}{ext}"

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
        cookies_browser = None
        cookies_found = False
        # First try to get cookies from browsers
        for browser in ['chrome', 'firefox', 'edge', 'opera', 'brave', 'chromium']:
            try:
                with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                    cookies = ydl.cookiejar.get_cookies_from_browser(browser)
                    if cookies:
                        self.log(f"Using cookies from {browser.title()}")
                        cookies_browser = browser  # Save working browser
                        cookies_found = True  # Mark that we found cookies
                        break
            except Exception as e:
                self.log(f"Could not get cookies from {browser}")
                continue

        if not cookies_found:
            self.log(
                "Warning: No cookies found from any browser. This may affect video availability.")

        # Prepare yt-dlp options with reliable settings
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
            'ffmpeg_location': 'ffmpeg',
            'nocheckcertificate': True,
            'http_chunk_size': 10485760,
            'retries': 10,
            'fragment_retries': 10,
            'file_access_retries': 10,
            'socket_timeout': 30,
            'merge_output_format': 'mp4',
            'cookiesfrombrowser': (cookies_browser,) if cookies_browser else None,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'DNT': '1'
            }
        }

        # Handle audio-only downloads
        if self.quality_var.get() == "Audio Only (MP3)":
            ydl_opts.update({
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'format': 'bestaudio/best',  # Override format for audio-only
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

                            # Get video info first with retries
                            max_retries = 5
                            retry_count = 0
                            info = None
                            last_error = None

                            while retry_count < max_retries:
                                try:
                                    self.log(
                                        f"Fetching info for video {i} (attempt {retry_count + 1})...")
                                    info = ydl.extract_info(
                                        url, download=False)
                                    if info:  # Successfully got info
                                        break
                                except Exception as e:
                                    error_msg = str(e)
                                    retry_count += 1

                                    if retry_count < max_retries:
                                        self.log(
                                            f"Retry {retry_count}/{max_retries} - Error: {error_msg}")

                                        # Always rotate user agent on retry for better success rate
                                        user_agents = [
                                            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                                            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Edg/119.0.0.0',
                                            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
                                            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 OPR/105.0.0.0',
                                            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
                                        ]
                                        # Update user agent
                                        ydl_opts['http_headers']['User-Agent'] = user_agents[retry_count % len(
                                            user_agents)]

                                        # Add random delay between retries
                                        import random
                                        import time
                                        delay = random.uniform(1.0, 3.0)
                                        self.log(
                                            f"Waiting {delay:.1f} seconds before retry...")
                                        time.sleep(delay)
                                        continue
                                    else:
                                        self.log(
                                            f"Failed after {max_retries} attempts. Last error: {error_msg}")
                                        break

                            if not info:
                                self.log(
                                    f"❌ Could not fetch info for URL: {url}")
                                continue title = info.get('title', 'Unknown Title')
                            duration = info.get('duration')
                            filesize = info.get('filesize')

                            # Log video details
                            self.log(f"Found: {title}")
                            if duration:
                                self.log(
                                    f"Duration: {int(duration/60)}m {duration % 60}s")
                            if filesize:
                                self.log(
                                    f"Expected size: {filesize/1024/1024:.1f}MB")

                            # Update output template with clean filename
                            clean_title = self.clean_filename(
                                title, i if len(urls) > 1 else None)
                            ydl_opts['outtmpl'] = os.path.join(
                                self.download_path,
                                clean_title + '.%(ext)s'
                            )

                            # Create new YoutubeDL instance with updated options
                            self.log(f"Starting download: {clean_title}")
                            with yt_dlp.YoutubeDL(ydl_opts) as ydl_single:
                                ydl_single.download([url])

                            # Verify the download
                            expected_file = os.path.join(
                                self.download_path,
                                clean_title + '.mp4'  # Since we're forcing MP4 output
                            )

                            if os.path.exists(expected_file):
                                file_size = os.path.getsize(expected_file)
                                self.log(
                                    f"✅ Successfully downloaded: {clean_title} ({file_size/1024/1024:.1f}MB)")
                            else:
                                self.log(
                                    f"⚠️ Download completed but file not found: {clean_title}")

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

    # Set a custom style
    style = ttk.Style()
    style.theme_use('clam')

    # Configure color scheme
    style.configure('TLabelframe', background='#f0f0f0')
    style.configure('TLabelframe.Label', font=('Helvetica', 10))

    # Configure custom button style with more prominent appearance
    style.configure('Accent.TButton',
                    font=('Helvetica', 11, 'bold'),
                    padding=10,
                    background='#0066cc',
                    foreground='white')

    # Style when mouse hovers over the button
    style.map('Accent.TButton',
              background=[('active', '#0052a3')],
              foreground=[('active', 'white')])

    app = YoutubeDownloader(root)
    root.mainloop()


if __name__ == "__main__":
    main()
