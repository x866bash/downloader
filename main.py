import os
import requests
from bs4 import BeautifulSoup
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------- Konfigurasi ----------
BASE_URL = "https://archive.org/download/NS-326-350"
OUTPUT_DIR = "downloads"
MAX_PARALLEL_DOWNLOADS = 5
SOCKET_TIMEOUT = 20
MAX_RETRIES = 5
EXTERNAL_DOWNLOADER = "aria2c"
EXTERNAL_DOWNLOADER_ARGS = "-x 16 -k 1M"  # 16 koneksi, 1MB per chunk


# ---------- Helper Functions ----------
def get_mp4_links(url):
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        return [], f"[ERROR] Gagal membuka {url}: {e}"
    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        if a["href"].lower().endswith(".mp4"):
            links.append(f"{url}/{a['href']}")
    return links, None


# ---------- GUI Class ----------
class DownloaderGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Archive.org MP4 Downloader")
        self.geometry("950x750")
        self.protocol("WM_DELETE_WINDOW", self.on_quit)
        self.create_widgets()
        self.executor = ThreadPoolExecutor(max_workers=MAX_PARALLEL_DOWNLOADS)
        self.lock = threading.Lock()
        self.base_url = BASE_URL

    def create_widgets(self):
        # Frame input URL
        self.frame_input = ttk.LabelFrame(self, text="Input Link Archive.org")
        self.frame_input.pack(fill=tk.X, padx=5, pady=5)

        self.entry_url = ttk.Entry(self.frame_input, width=80)
        self.entry_url.insert(0, BASE_URL)
        self.entry_url.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_set_url = ttk.Button(self.frame_input, text="Set Link", command=self.set_url)
        self.btn_set_url.pack(side=tk.LEFT, padx=5)

        self.btn_check = ttk.Button(self.frame_input, text="Check Files", command=self.check_files)
        self.btn_check.pack(side=tk.LEFT, padx=5)

        self.btn_download_missing = ttk.Button(self.frame_input, text="Download Missing Only",
                                               command=self.download_missing_from_check)
        self.btn_download_missing.pack(side=tk.LEFT, padx=5)

        # Frame untuk progress
        self.frame_progress = ttk.LabelFrame(self, text="Download Progress (Maks 5 File)")
        self.frame_progress.pack(fill=tk.BOTH, expand=False, padx=5, pady=5)

        self.progress_bars = []
        self.progress_labels = []
        for i in range(MAX_PARALLEL_DOWNLOADS):
            lbl = ttk.Label(self.frame_progress, text=f"File {i+1}: ")
            lbl.grid(row=i, column=0, sticky="w", padx=5, pady=2)
            pb = ttk.Progressbar(self.frame_progress, length=700)
            pb.grid(row=i, column=1, sticky="ew", padx=5, pady=2)
            self.progress_labels.append(lbl)
            self.progress_bars.append(pb)

        # Frame utama bawah
        self.frame_bottom = ttk.Frame(self)
        self.frame_bottom.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Frame log
        self.frame_log = ttk.LabelFrame(self.frame_bottom, text="Output Log")
        self.frame_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.text_log = scrolledtext.ScrolledText(self.frame_log, wrap=tk.WORD, height=15)
        self.text_log.pack(fill=tk.BOTH, expand=True)
        self.text_log.bind("<Key>", lambda e: "break")
        self.text_log.bind("<Button-1>", lambda e: None)

        # Frame file selesai
        self.frame_done = ttk.LabelFrame(self.frame_bottom, text="Downloaded Files")
        self.frame_done.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.text_done = scrolledtext.ScrolledText(self.frame_done, wrap=tk.WORD, height=15)
        self.text_done.pack(fill=tk.BOTH, expand=True)
        self.text_done.bind("<Key>", lambda e: "break")
        self.text_done.bind("<Button-1>", lambda e: None)

        # Tombol start
        self.btn_start = ttk.Button(self, text="Start Download", command=self.start_download)
        self.btn_start.pack(pady=5)

    def set_url(self):
        self.base_url = self.entry_url.get().strip()
        self.log(f"[INFO] URL diatur ke: {self.base_url}")

    def check_files(self):
        self.log("Mengecek file MP4 yang sudah terdownload...")
        links, err = get_mp4_links(self.base_url)
        if err:
            self.log(err)
            return
        if not links:
            self.log("[ERROR] Tidak ditemukan file MP4 di link.")
            return

        total = len(links)
        downloaded = 0
        self.missing_links = []

        for link in links:
            filename = os.path.join(OUTPUT_DIR, os.path.basename(link))
            if os.path.exists(filename):
                downloaded += 1
            else:
                self.missing_links.append(link)
                self.log(f"[MISSING] {os.path.basename(link)}")

        self.log(f"[CHECK] {downloaded}/{total} file sudah terdownload.")

        if not self.missing_links:
            messagebox.showinfo("Check Files", "Semua file sudah terdownload ✔")
        else:
            messagebox.showwarning("Check Files",
                                   f"{downloaded} dari {total} file sudah ada.\n"
                                   f"{len(self.missing_links)} file masih hilang.")

    def download_missing_from_check(self):
        if not hasattr(self, "missing_links") or not self.missing_links:
            messagebox.showinfo("Download Missing", "Tidak ada file yang hilang untuk diunduh.")
            return
        threading.Thread(target=self.download_missing, args=(self.missing_links,)).start()

    def download_missing(self, missing_links):
        self.log(f"[INFO] Mendownload ulang {len(missing_links)} file yang belum terdownload...")
        futures = []
        for i, url in enumerate(missing_links):
            idx = i % MAX_PARALLEL_DOWNLOADS
            futures.append(self.executor.submit(self.download_file, url, idx))

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                self.log(f"[EXCEPTION] {e}")

        self.log("[INFO] Download ulang selesai.")

    def log(self, message):
        with self.lock:
            self.text_log.configure(state='normal')
            self.text_log.insert(tk.END, message + "\n")
            self.text_log.see(tk.END)
            self.text_log.configure(state='disabled')

    def add_done_file(self, message):
        with self.lock:
            self.text_done.configure(state='normal')
            self.text_done.insert(tk.END, message + "\n")
            self.text_done.see(tk.END)
            self.text_done.configure(state='disabled')

    def start_download(self):
        self.btn_start.config(state=tk.DISABLED)
        threading.Thread(target=self.download_all).start()

    def download_file(self, url, index):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        attempt = 0
        while attempt < MAX_RETRIES:
            attempt += 1
            command = [
                "yt-dlp",
                "--external-downloader", EXTERNAL_DOWNLOADER,
                "--external-downloader-args", EXTERNAL_DOWNLOADER_ARGS,
                "--socket-timeout", str(SOCKET_TIMEOUT),
                "--retries", "3",
                "--fragment-retries", "3",
                "--continue",
                "--newline",
                "-o", os.path.join(OUTPUT_DIR, "%(title)s.%(ext)s"),
                url
            ]
            try:
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                filename = None
                for line in iter(process.stdout.readline, ''):
                    line = line.strip()
                    if line.startswith("[download] Destination:"):
                        filename = line.replace("[download] Destination: ", "")
                        self.log(f"[INFO] [Download] Destination: {filename}")
                        self.progress_labels[index].config(text=f"{os.path.basename(filename)}")
                    elif "[download]" in line and "%" in line:
                        try:
                            parts = line.split()
                            percent = float(parts[1].replace("%", ""))
                            self.progress_bars[index]['value'] = percent
                        except:
                            pass
                    elif "ERROR" in line or "failed" in line.lower():
                        self.log(f"[ERROR] {line}")
                process.wait()
                if process.returncode == 0:
                    self.progress_bars[index]['value'] = 100
                    self.log(f"[INFO] [Download] Selesai: {filename}")
                    self.add_done_file(f"[INFO DOWNLOAD] {os.path.basename(filename)} [SUKSES] ✔")
                    break
                else:
                    self.log(f"[ERROR] Sinyal anda lemot!!! Mengulang download... (Percobaan {attempt}/{MAX_RETRIES})")
            except Exception as e:
                self.log(f"[EXCEPTION] {e}")
                self.log(f"[ERROR] Mengulang download... (Percobaan {attempt}/{MAX_RETRIES})")
        else:
            self.log(f"[ERROR] Download gagal untuk: {url} setelah {MAX_RETRIES} percobaan")

    def download_all(self):
        self.log("Mencari file MP4 di archive.org...")
        links, err = get_mp4_links(self.base_url)
        if err:
            self.log(err)
            self.btn_start.config(state=tk.NORMAL)
            return
        if not links:
            self.log("[ERROR] Tidak ditemukan file MP4.")
            self.btn_start.config(state=tk.NORMAL)
            return
        self.log(f"Ditemukan {len(links)} file MP4. Mulai download paralel maksimal {MAX_PARALLEL_DOWNLOADS} file...")

        futures = []
        for i, url in enumerate(links):
            idx = i % MAX_PARALLEL_DOWNLOADS
            futures.append(self.executor.submit(self.download_file, url, idx))

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                self.log(f"[EXCEPTION] {e}")

        self.log("Semua file MP4 selesai didownload.")
        self.btn_start.config(state=tk.NORMAL)

    def on_quit(self):
        if messagebox.askokcancel("Quit", "Apakah Anda yakin ingin keluar?"):
            self.executor.shutdown(wait=False)
            self.destroy()


# ---------- Main ----------
if __name__ == "__main__":
    app = DownloaderGUI()
    app.mainloop()

