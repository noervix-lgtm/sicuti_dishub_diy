# Sistem Informasi Pengelolaan Cuti Pegawai (lokal)

## Cara tercepat (Windows)
Ekstrak SEMUA isi zip (klik kanan > Extract All), lalu klik dua kali `JALANKAN.bat`. Browser terbuka otomatis.
Pertama kali butuh internet untuk memasang library.

## Cara manual (Windows PowerShell)
1. Pasang Python (centang "Add python.exe to PATH") dan buka folder ini di PowerShell.
2. Buat virtual environment dan pasang library (cukup sekali):
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   (Jika Activate diblokir: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned)
3. Jalankan:  python app.py
4. Buka browser: http://127.0.0.1:5000

## Login awal
- Admin: username `admin`, password `admin123`  -> LANGSUNG ganti lewat tombol "Ganti Password".
- Pegawai: username = NIP, password awal = NIP (setelah import Excel).

## Langkah pertama
1. Login admin -> Pengaturan -> Nama Instansi (cek isinya).
2. Pengaturan -> Hari Libur: isi libur nasional/cuti bersama (tidak dihitung sebagai cuti).
3. Pengaturan -> Import Excel -> unggah KARTU CUTI PNS.xlsx -> Periksa Struktur -> Import.
4. Cek Data Pegawai. Jika kolom Excel tidak terbaca, kirim struktur kolomnya agar penyesuaian dibuat.

## Aturan yang dipakai
- Jumlah hari = hari kerja (Senin-Jumat) dikurangi hari libur terdaftar.
- Hanya "Cuti Tahunan" yang memotong jatah. Jenis lain bisa diubah di JENIS_CUTI pada app.py.
- Jatah baru = 12 + pembulatan ke atas (sisa tahun lalu / 2), lewat menu "Buat Tahun Cuti Baru".
- Cuti tidak boleh melewati pergantian tahun (ajukan terpisah).

## Pengujian & backup
- `python tes_otomatis.py` menjalankan seluruh skenario uji dengan database sementara.
- Backup: salin file `database.db` dan folder `uploads/` secara rutin.
