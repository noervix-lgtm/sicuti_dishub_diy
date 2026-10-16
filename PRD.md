# PRD — Sistem Informasi Cuti Pegawai
**Instansi:** Dinas Perhubungan Daerah Istimewa Yogyakarta
**Versi:** 1.0 · **Status:** Draft siap dibangun

## 1. Tujuan
Menggantikan pengisian manual formulir cuti dan kartu cuti. Pegawai/operator cukup menginput data **satu kali**; sistem otomatis:
1. mengisi **Formulir Permintaan dan Pemberian Cuti** persis sesuai input,
2. mengisi **Kartu Cuti (Model Fe.03)** dan menghitung saldo cuti,
3. menampilkan keduanya dalam satu hasil cetak siap print (A4).

Tidak boleh ada input manual ulang di surat maupun kartu.

## 2. Referensi (wajib dibaca agen)
- `sistem_cuti.html` — prototipe yang sudah berjalan. **Tata letak cetak formulir & kartu harus mengikuti prototipe ini.**
- `SURAT_CUTI_UMUM.docx` — contoh surat dan kartu asli yang dipakai kantor.

## 3. Peran Pengguna (Role)
| Role | Hak akses |
|---|---|
| **Admin** | Kelola pengguna, data pegawai, pengaturan pejabat, cadangan data |
| **Operator Kepegawaian** | Input & ubah data cuti semua pegawai, cetak formulir + kartu, kelola saldo awal |
| **Atasan Langsung** | Melihat dan memberi pertimbangan (Disetujui/Perubahan/Ditangguhkan/Tidak Disetujui) untuk bawahannya |
| **Kepala Dinas (Pejabat)** | Memberi keputusan akhir atas permohonan |
| **Pegawai** | Mengajukan cuti, melihat saldo dan riwayat cuti sendiri, cetak formulirnya sendiri |

## 4. Alur Proses
1. Pegawai/Operator mengisi permohonan cuti.
2. Status **Diajukan** → atasan langsung memberi pertimbangan.
3. Status **Diproses** → Kepala Dinas memberi keputusan.
4. Status **Disetujui / Ditolak / Ditangguhkan / Perubahan**.
5. Jika disetujui (cuti tahunan), saldo berkurang dan baris baru masuk Kartu Cuti otomatis.
6. Operator mencetak formulir + kartu.

Operator boleh mengisi langsung hasil pertimbangan/keputusan (untuk kantor yang masih menandatangani manual).

## 5. Fitur
### 5.1 Data Pegawai
Nama (beserta gelar), NIP, jabatan, masa kerja, unit kerja, alamat, telepon, atasan langsung. Pegawai yang sudah tersimpan tinggal dipilih (data terisi otomatis).

### 5.2 Permohonan Cuti
Tanggal surat, nomor surat, jenis cuti, alasan, tanggal mulai, tanggal selesai, lama cuti, penyambung tanggal ("s.d." atau "dan"), alamat dan telepon selama cuti.

Jenis cuti: Tahunan, Besar, Sakit, Melahirkan, Karena Alasan Penting, di Luar Tanggungan Negara.

### 5.3 Hitung Otomatis
- **Lama cuti** = jumlah hari kerja (tanpa Sabtu/Minggu) antara tanggal mulai dan selesai; bisa diubah manual (mis. libur nasional). Sebaiknya ada tabel hari libur nasional yang dikelola Admin.
- **Saldo cuti tahunan:**
  - Hak tahun berjalan = 12 hari.
  - Carry over = sisa tahun lalu dibagi 2, dibulatkan ke bawah, maksimal 6 hari: `min(floor(sisa tahun lalu / 2), 6)`.
  - Hak total = 12 + carry over.
  - Sisa = hak total − total cuti tahunan yang diambil tahun itu (berurutan menurut tanggal).
- **Catatan Cuti pada formulir:** N-1 = sisa tahun lalu yang belum terpakai, N = sisa jatah tahun berjalan, sebelum cuti yang sedang diajukan.
- Cuti selain tahunan tidak mengurangi saldo cuti tahunan dan tidak masuk Kartu Cuti.

### 5.4 Cetak
Satu tombol cetak menghasilkan 2 halaman A4:
- **Halaman 1 — Formulir Permintaan dan Pemberian Cuti:** I Data Pegawai, II Jenis Cuti (tanda V), III Alasan, IV Lamanya Cuti, V Catatan Cuti (jenis terpilih di nomor 1, sisanya urut 2–6), VI Alamat selama cuti + tanda tangan pegawai, VII Pertimbangan Atasan Langsung, VIII Keputusan Pejabat.
- **Halaman 2 — Kartu Cuti Fe.03:** baris awal tahun (Awal tahun 12 hr, Sisa tahun lalu, Cuti Th ini), lalu satu baris per cuti tahunan: pejabat, nomor & tanggal surat, lama cuti, tanggal cuti, hak/ambil/sisa.

Semua isi diambil dari data tersimpan, tanpa pengetikan ulang. Tampilan layar harus sama dengan hasil cetak (pratinjau).

### 5.5 Riwayat, Pencarian, dan Rekap
- Daftar semua permohonan (filter: pegawai, tahun, jenis, status).
- Rekap saldo cuti seluruh pegawai per tahun.
- Ekspor rekap ke Excel.

### 5.6 Impor Data Awal
Impor data pegawai dan riwayat cuti dari `SURAT_CUTI_UMUM.docx` / Excel, termasuk saldo awal (sisa tahun lalu) per pegawai.

### 5.7 Pengaturan
Nama dan NIP Kepala Dinas, nama unit kerja, format nomor surat, hari libur nasional, pengguna dan role.

## 6. Struktur Database (usulan)
- `users` (id, nama, username, password_hash, role, pegawai_id)
- `pegawai` (id, nip, nama, jabatan, unit_kerja, masa_kerja, alamat, telp, atasan_id)
- `saldo_cuti` (id, pegawai_id, tahun, sisa_tahun_lalu) — unik per pegawai + tahun
- `cuti` (id, pegawai_id, jenis, tanggal_surat, nomor_surat, alasan, tgl_mulai, tgl_selesai, penyambung, lama_hari, alamat_cuti, telp_cuti, atasan_nama, atasan_nip, pertimbangan_atasan, keputusan_pejabat, status, created_by, created_at)
- `hari_libur` (id, tanggal, keterangan)
- `pengaturan` (kunci, nilai)
- `log_aktivitas` (id, user_id, aksi, objek, waktu)

Saldo dan baris Kartu Cuti dihitung dari tabel `cuti` + `saldo_cuti`, tidak disimpan ganda.

## 7. Kebutuhan Non-Fungsional
- Login wajib; password di-hash; sesi berakhir otomatis.
- Pembatasan data per role (pegawai hanya melihat datanya sendiri).
- Data pegawai bersifat pribadi: tidak boleh bisa diakses tanpa login.
- Cadangan database terjadwal dan ekspor manual.
- Responsif (HP dan desktop); hasil cetak tetap A4 yang rapi.
- Bahasa antarmuka: Indonesia. Format tanggal: `30 September 2026`.

## 8. Arah Tampilan (UI/UX)
Mengikuti gaya aplikasi pemerintahan Indonesia: bersih, resmi, mudah dibaca.
- Palet biru tua/putih, tanpa dekorasi berlebihan, kontras tinggi.
- Header berisi nama instansi dan nama aplikasi.
- Form bertahap dengan label jelas, validasi tanggal dan NIP, pesan kesalahan berbahasa Indonesia.
- Pratinjau formulir dan kartu tampil langsung di samping form.
- Tabel dengan pencarian, filter, dan paginasi.

## 9. Teknologi
> **Diisi sesuai hosting yang dipakai.** Usulan awal: Laravel (PHP) + MySQL untuk hosting cPanel; atau Node.js + SQLite/PostgreSQL untuk VPS. Agen boleh mengusulkan alternatif sebelum membangun.

## 10. Kriteria Selesai
- [ ] Input satu kali menghasilkan formulir dan kartu yang identik dengan data input.
- [ ] Saldo cuti tahunan benar (carry over maksimal 6 hari, pengurangan berurutan).
- [ ] Hasil cetak 2 halaman A4 sama dengan `sistem_cuti.html`.
- [ ] Kelima role bekerja sesuai hak akses.
- [ ] Data pegawai dan riwayat dari file Word berhasil diimpor.
- [ ] Bisa berjalan di localhost dan di hosting.
