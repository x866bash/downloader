# Archive.org MP4 Downloader (Versi GUI)

Alat sederhana dengan antarmuka GUI untuk mendownload file MP4 dari archive.org dengan progress real-time, retry otomatis, dan tampilan log.

## Fitur

- Download banyak file MP4 secara paralel (maksimal 5 file sekaligus)
- Progress bar real-time untuk file yang sedang didownload
- Retry otomatis jika download gagal atau koneksi internet lambat
- Log output untuk semua aktivitas download
- Panel untuk melihat file yang sudah berhasil didownload dengan status `[SUKSES] ✔`
- Panel log dan daftar file selesai dapat digulir (scrollable)
- Log dapat disalin (copyable)

## Persyaratan

- Python 3.8+
- `requests`
- `beautifulsoup4`
- `yt-dlp`
- `aria2c`
- `tkinter`

Install dependencies Python:

```bash
pip install requests beautifulsoup4 yt-dlp
```

Pastikan aria2c sudah terinstall di sistem Anda.

Contoh untuk Ubuntu/Debian:
```bash
sudo apt install aria2
```

## Cara Menggunakan
1. Clone atau download repository ini.
2. Edit pada bagian script `main.py` ganti link yang lu mau download pada bagian konfigurasi, kalo gk tau cari sendiri TOT.
3. Jalankan GUI:
```bash
python main.py
```
4. Klik Start Download untuk memulai download file MP4 dari URL archive.org yang sudah ditentukan.
5. Pantau progress di panel atas, log di panel kiri bawah, dan file yang sudah selesai di panel kanan bawah.

---

## Konfigurasi

Anda bisa mengedit `main.py` untuk mengubah:
- `BASE_URL` → URL folder archive.org yang ingin didownload
- `OUTPUT_DIR` → Folder untuk menyimpan file yang didownload
- `MAX_PARALLEL_DOWNLOADS` → Jumlah download simultan
- `SOCKET_TIMEOUT` → Waktu timeout download dalam detik
- `MAX_RETRIES` → Jumlah percobaan ulang per file
- `EXTERNAL_DOWNLOADER_ARGS` → Opsi untuk downloader 'aria2c'

---

## Lisensi
Project ini open source dengan lisensi MIT.
Check dokumen [LICENSE](https://raw.githubusercontent.com/x866bash/downloader/refs/heads/main/LICENSE)

---
**Dokumen ini saya buat dengan terburu buru karena ingin menonton anime naruto yang berada di archive.org**
---
