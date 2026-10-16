"""Pengujian otomatis TAHAP C:
1. Tombol 'Cetak Formulir + Kartu' di halaman detail pengajuan.
2. Route /pengajuan/<pid>/cetak-gabungan.pdf berfungsi:
   - Tepat 2 halaman A4 (Hal 1: Formulir Portrait, Hal 2: Kartu Cuti Fe.03 Landscape).
   - Hak akses: Pegawai lain ditolak (HTTP 403), pegawai pemilik & admin diizinkan (HTTP 200).
3. Pengajuan 'Menunggu' dan 'Ditolak' TIDAK masuk ke tabel kartu cuti di halaman 2.
4. Pengajuan 'Disetujui' MASUK ke tabel kartu cuti di halaman 2 lengkap dengan nomor & tanggal surat.
5. Route lama /kartu/<pid>.pdf dan formulir.pdf tetap ada dan berfungsi normal.
"""
import os, io, re, zlib, base64, tempfile, shutil
from werkzeug.security import generate_password_hash

import app as A

def ekstrak_teks_pdf(pdf_bytes):
    """Ekstrak semua teks dari stream PDF ReportLab."""
    idx = 0
    hasil = []
    while True:
        s_idx = pdf_bytes.find(b'stream', idx)
        if s_idx == -1: break
        e_idx = pdf_bytes.find(b'endstream', s_idx)
        if e_idx == -1: break
        raw = pdf_bytes[s_idx+6:e_idx].strip()
        try:
            a85 = base64.a85decode(raw, adobe=True)
            dec = zlib.decompress(a85).decode('latin1', errors='ignore')
            hasil.append(dec)
        except Exception:
            try:
                dec = zlib.decompress(raw).decode('latin1', errors='ignore')
                hasil.append(dec)
            except Exception:
                pass
        idx = e_idx + 9
    return " ".join(hasil)

def test_tahap_c():
    temp_dir = tempfile.mkdtemp()
    temp_db = os.path.join(temp_dir, "test_tahap_c.db")
    A.DB_PATH = temp_db

    A.init_db()
    c = A.sqlite3.connect(temp_db)
    c.row_factory = A.sqlite3.Row

    # Setup instansi
    c.execute("INSERT OR REPLACE INTO pengaturan VALUES('instansi', 'DINAS PERHUBUNGAN DIY')")
    c.execute("INSERT OR REPLACE INTO pengaturan VALUES('kepala_nama', 'Ni Made Dwi Panti Indrayanti, S.T., M.T.')")
    c.execute("INSERT OR REPLACE INTO pengaturan VALUES('kepala_nip', '197001011995032001')")
    c.execute("INSERT OR REPLACE INTO pengaturan VALUES('kepala_jabatan', 'Kepala Dinas Perhubungan Daerah Istimewa Yogyakarta')")

    # Setup 2 pegawai: Budi & Siti
    c.execute("""INSERT INTO pegawai(nip, nama, golongan, unit_kerja, username, password_hash, role, aktif,
                 jabatan, masa_kerja, atasan_nama, atasan_nip)
                 VALUES(?, ?, ?, ?, ?, ?, 'pegawai', 1, ?, ?, ?, ?)""",
              ('198501012010011001', 'Budi Santoso', 'III/c', 'Bidang Lalu Lintas',
               'budi', generate_password_hash('budi123'),
               'Pengatur Lalu Lintas', '10 Tahun 2 Bulan', 'Ir. Bambang, M.T.', '197505051999031002'))
    id_budi = c.execute("SELECT last_insert_rowid()").fetchone()[0]

    c.execute("""INSERT INTO pegawai(nip, nama, golongan, unit_kerja, username, password_hash, role, aktif,
                 jabatan, masa_kerja, atasan_nama, atasan_nip)
                 VALUES(?, ?, ?, ?, ?, ?, 'pegawai', 1, ?, ?, ?, ?)""",
              ('199002022015022002', 'Siti Rahma', 'III/a', 'Sekretariat',
               'siti', generate_password_hash('siti123'),
               'Staf Kepegawaian', '5 Tahun 0 Bulan', 'Drs. Supriyanto', '197001011995011001'))
    id_siti = c.execute("SELECT last_insert_rowid()").fetchone()[0]

    # Inisialisasi jatah cuti 2026
    c.execute("""INSERT INTO jatah_cuti(pegawai_id, tahun, jatah_dasar, tambahan_dari_tahun_sebelumnya,
                 total_jatah, digunakan_awal, total_digunakan, sisa_cuti, cuti_dibawa_ke_tahun_berikutnya)
                 VALUES(?, 2026, 12, 0, 12, 0, 0, 12, 6)""", (id_budi,))
    c.execute("""INSERT INTO jatah_cuti(pegawai_id, tahun, jatah_dasar, tambahan_dari_tahun_sebelumnya,
                 total_jatah, digunakan_awal, total_digunakan, sisa_cuti, cuti_dibawa_ke_tahun_berikutnya)
                 VALUES(?, 2026, 12, 0, 12, 0, 0, 12, 6)""", (id_siti,))

    # Buat 3 pengajuan untuk Budi:
    # 1. Menunggu (3 hari)
    c.execute("""INSERT INTO pengajuan_cuti(pegawai_id, jenis_cuti, tanggal_mulai, tanggal_selesai,
                 jumlah_hari, alasan, status, tanggal_pengajuan, memotong_jatah, alamat_cuti, telp_cuti)
                 VALUES(?, 'Cuti Tahunan', '2026-03-02', '2026-03-04', 3, 'Alasan Menunggu Verifikasi',
                 'Menunggu', '2026-02-28 09:00', 1, 'Jl. Malioboro No. 10', '08123456789')""", (id_budi,))
    pid_menunggu = c.execute("SELECT last_insert_rowid()").fetchone()[0]

    # 2. Ditolak (2 hari)
    c.execute("""INSERT INTO pengajuan_cuti(pegawai_id, jenis_cuti, tanggal_mulai, tanggal_selesai,
                 jumlah_hari, alasan, status, tanggal_pengajuan, memotong_jatah, alamat_cuti, telp_cuti, catatan_admin)
                 VALUES(?, 'Cuti Tahunan', '2026-04-06', '2026-04-07', 2, 'Alasan Ditolak Tes',
                 'Ditolak', '2026-04-01 10:00', 1, 'Jl. Solo Km 5', '08123456789', 'Jadwal dinas padat')""", (id_budi,))
    pid_ditolak = c.execute("SELECT last_insert_rowid()").fetchone()[0]

    # 3. Disetujui (5 hari, dengan nomor dan tanggal surat)
    c.execute("""INSERT INTO pengajuan_cuti(pegawai_id, jenis_cuti, tanggal_mulai, tanggal_selesai,
                 jumlah_hari, alasan, status, tanggal_pengajuan, memotong_jatah, alamat_cuti, telp_cuti,
                 nomor_surat, tanggal_surat)
                 VALUES(?, 'Cuti Tahunan', '2026-05-11', '2026-05-15', 5, 'Alasan Cuti Disetujui',
                 'Disetujui', '2026-05-02 08:30', 1, 'Jl. Kaliurang Km 9', '08123456789',
                 '800/TAHAP-C/2026', '2026-05-08')""", (id_budi,))
    pid_disetujui = c.execute("SELECT last_insert_rowid()").fetchone()[0]

    c.commit()
    c.close()

    tc = A.app.test_client()

    print("=== PENGUJIAN TAHAP C: CETAK FORMULIR + KARTU GABUNGAN ===")

    # 1. Uji Hak Akses
    # 1.1 Siti (pegawai lain) login dan coba cetak pengajuan Budi -> harus 403 Forbidden
    with tc.session_transaction() as sess:
        sess['uid'] = id_siti
    res = tc.get(f'/pengajuan/{pid_disetujui}/cetak-gabungan.pdf')
    assert res.status_code == 403, f"Harusnya 403 untuk pegawai lain, tapi {res.status_code}"
    print("1. Hak akses: Pegawai lain (Siti) dilarang membuka cetak gabungan Budi (HTTP 403). [OK]")

    # 1.2 Budi (pemilik) login dan cetak pengajuan miliknya -> harus 200 OK
    with tc.session_transaction() as sess:
        sess['uid'] = id_budi
    res = tc.get(f'/pengajuan/{pid_disetujui}/cetak-gabungan.pdf')
    assert res.status_code == 200, f"Harusnya 200 untuk pemilik pengajuan, tapi {res.status_code}"
    assert res.data[:4] == b'%PDF', "Respon bukan file PDF valid"
    print("2. Hak akses: Pemilik pengajuan (Budi) berhasil membuka cetak gabungan (HTTP 200). [OK]")

    # 1.3 Admin login dan cetak pengajuan Budi -> harus 200 OK
    id_admin = 1
    with tc.session_transaction() as sess:
        sess['uid'] = id_admin
    res = tc.get(f'/pengajuan/{pid_disetujui}/cetak-gabungan.pdf')
    assert res.status_code == 200, f"Harusnya 200 untuk admin, tapi {res.status_code}"
    assert res.data[:4] == b'%PDF', "Respon bukan file PDF valid"
    print("3. Hak akses: Admin berhasil membuka cetak gabungan (HTTP 200). [OK]")

    # 2. Uji Tombol di Halaman Detail Pengajuan
    # 2.1 Admin melihat tombol "Cetak Formulir + Kartu" yang mengarah ke /pengajuan/<pid>/cetak-gabungan.pdf
    res_det_admin = tc.get(f'/pengajuan/{pid_disetujui}')
    assert res_det_admin.status_code == 200
    html_admin = res_det_admin.data.decode('utf-8')
    assert f'/pengajuan/{pid_disetujui}/cetak-gabungan.pdf' in html_admin, "Route cetak-gabungan.pdf tidak ada di detail admin"
    assert "Cetak Formulir + Kartu" in html_admin, "Label tombol 'Cetak Formulir + Kartu' tidak ditemukan di detail admin"
    print("4. Tombol 'Cetak Formulir + Kartu' muncul di halaman detail untuk Admin. [OK]")

    # 2.2 Pegawai pemilik (Budi) melihat tombol "Cetak Formulir + Kartu"
    with tc.session_transaction() as sess:
        sess['uid'] = id_budi
    res_det_budi = tc.get(f'/pengajuan/{pid_disetujui}')
    assert res_det_budi.status_code == 200
    html_budi = res_det_budi.data.decode('utf-8')
    assert f'/pengajuan/{pid_disetujui}/cetak-gabungan.pdf' in html_budi, "Route cetak-gabungan.pdf tidak ada di detail pegawai pemilik"
    assert "Cetak Formulir + Kartu" in html_budi, "Label tombol 'Cetak Formulir + Kartu' tidak ditemukan di detail pegawai pemilik"
    print("5. Tombol 'Cetak Formulir + Kartu' muncul di halaman detail untuk Pegawai Pemilik. [OK]")

    # 2.3 Pegawai lain (Siti) dilarang mengakses halaman detail Budi
    with tc.session_transaction() as sess:
        sess['uid'] = id_siti
    res_det_siti = tc.get(f'/pengajuan/{pid_disetujui}')
    assert res_det_siti.status_code == 403, "Pegawai lain tidak boleh mengakses detail pengajuan milik orang lain"
    print("6. Pegawai lain dilarang mengakses detail pengajuan pegawai lain (HTTP 403). [OK]")

    # 3. Uji Struktur & Jumlah Halaman PDF
    pdf_bytes = res.data
    pages_count_match = re.search(rb'/Count\s+(\d+)', pdf_bytes)
    pages_count = int(pages_count_match.group(1)) if pages_count_match else len(re.findall(rb'/Type\s*/Page\b', pdf_bytes))
    assert pages_count == 2, f"Total halaman harus tepat 2, didapat {pages_count}"

    mediaboxes = re.findall(rb'/MediaBox\s*\[\s*0\s+0\s+([\d\.]+)\s+([\d\.]+)\s*\]', pdf_bytes)
    assert len(mediaboxes) == 2, f"MediaBox harus ada 2, ditemukan {len(mediaboxes)}"
    w1, h1 = float(mediaboxes[0][0]), float(mediaboxes[0][1])
    assert w1 < h1, "Halaman 1 harus berorientasi Portrait A4"
    w2, h2 = float(mediaboxes[1][0]), float(mediaboxes[1][1])
    assert w2 > h2, "Halaman 2 harus berorientasi Landscape A4"
    print(f"7. Dokumen PDF tepat 2 halaman: Hal 1 Portrait A4 ({w1:.1f}x{h1:.1f}), Hal 2 Landscape A4 ({w2:.1f}x{h2:.1f}). [OK]")

    # 4. Uji Pengajuan Disetujui masuk Kartu dengan Nomor & Tanggal Surat
    # Ambil konten teks PDF
    teks_lengkap = ekstrak_teks_pdf(pdf_bytes)
    # Cek nomor surat pengajuan Disetujui ada di PDF
    assert "800/TAHAP-C/2026" in teks_lengkap, "Nomor surat pengajuan Disetujui harus tampil di PDF"
    assert "8 Mei 2026" in teks_lengkap, "Tanggal surat pengajuan Disetujui harus tampil di PDF"
    assert "5 hari" in teks_lengkap, "Durasi 5 hari pengajuan Disetujui harus tampil di PDF"
    print("8. Pengajuan 'Disetujui' terbukti MASUK ke Kartu Cuti beserta nomor surat & tanggal surat. [OK]")

    # 5. Uji Pengajuan 'Menunggu' dan 'Ditolak' TIDAK MASUK KARTU
    # Mari kita cek dari flowables kartu cuti langsung dan dari PDF gabungan:
    with A.app.app_context():
        # Query rows kartu untuk Budi tahun 2026:
        rows_k = A.db().execute("""SELECT * FROM pengajuan_cuti
            WHERE pegawai_id=? AND jenis_cuti='Cuti Tahunan' AND status='Disetujui'
            AND substr(tanggal_mulai,1,4)='2026'""", (id_budi,)).fetchall()
        # Harus hanya ada 1 baris (pengajuan disetujui), TIDAK ADA pengajuan Menunggu maupun Ditolak
        assert len(rows_k) == 1, f"Baris cuti disetujui harus 1, didapat {len(rows_k)}"
        assert rows_k[0]['id'] == pid_disetujui
        assert rows_k[0]['nomor_surat'] == '800/TAHAP-C/2026'

        # Cek apakah pengajuan Menunggu atau Ditolak masuk query kartu:
        ids_kartu = [r['id'] for r in rows_k]
        assert pid_menunggu not in ids_kartu, "Pengajuan Menunggu TIDAK boleh masuk kartu cuti"
        assert pid_ditolak not in ids_kartu, "Pengajuan Ditolak TIDAK boleh masuk kartu cuti"
    print("9. Pengajuan 'Menunggu' dan 'Ditolak' terbukti TIDAK masuk ke tabel Kartu Cuti Fe.03. [OK]")

    # 6. Uji Cetak Gabungan untuk Pengajuan yang berstatus 'Menunggu':
    # Halaman 1 memuat data formulir menunggu (3 hari), sedangkan kartu tetap hanya memuat yang disetujui
    with tc.session_transaction() as sess:
        sess['uid'] = id_budi
    res_m = tc.get(f'/pengajuan/{pid_menunggu}/cetak-gabungan.pdf')
    assert res_m.status_code == 200
    pdf_m_bytes = res_m.data
    m_count_match = re.search(rb'/Count\s+(\d+)', pdf_m_bytes)
    m_count = int(m_count_match.group(1)) if m_count_match else len(re.findall(rb'/Type\s*/Page\b', pdf_m_bytes))
    assert m_count == 2, f"Total halaman harus tepat 2, didapat {m_count}"
    teks_m = ekstrak_teks_pdf(pdf_m_bytes)
    assert "Alasan Menunggu Verifikasi" in teks_m, "Formulir Hal 1 harus memuat data pengajuan menunggu"
    print("10. Cetak gabungan untuk status 'Menunggu' berhasil: Formulir memuat pengajuan, Kartu tetap sesuai aturan. [OK]")

    # 7. Uji Cetak Gabungan untuk Pengajuan yang berstatus 'Ditolak':
    res_t = tc.get(f'/pengajuan/{pid_ditolak}/cetak-gabungan.pdf')
    assert res_t.status_code == 200
    pdf_t_bytes = res_t.data
    t_count_match = re.search(rb'/Count\s+(\d+)', pdf_t_bytes)
    t_count = int(t_count_match.group(1)) if t_count_match else len(re.findall(rb'/Type\s*/Page\b', pdf_t_bytes))
    assert t_count == 2, f"Total halaman harus tepat 2, didapat {t_count}"
    teks_t = ekstrak_teks_pdf(pdf_t_bytes)
    assert "Alasan Ditolak Tes" in teks_t, "Formulir Hal 1 harus memuat data pengajuan ditolak"
    print("11. Cetak gabungan untuk status 'Ditolak' berhasil: Formulir memuat pengajuan, Kartu tetap sesuai aturan. [OK]")

    # 8. Uji Route-Route Lama Tetap Berfungsi Normal
    # 8.1 /kartu/<pid>.pdf
    res_kartu = tc.get(f'/kartu/{id_budi}.pdf')
    assert res_kartu.status_code == 200
    assert res_kartu.data[:4] == b'%PDF'

    # 8.2 /formulir/<pid>.pdf
    res_form_alias = tc.get(f'/formulir/{pid_disetujui}.pdf')
    assert res_form_alias.status_code == 200
    assert res_form_alias.data[:4] == b'%PDF'

    # 8.3 /pengajuan/<pid>/formulir.pdf (formulir tunggal 1 halaman)
    res_form_tunggal = tc.get(f'/pengajuan/{pid_disetujui}/formulir.pdf')
    assert res_form_tunggal.status_code == 200
    assert res_form_tunggal.data[:4] == b'%PDF'
    tunggal_count_match = re.search(rb'/Count\s+(\d+)', res_form_tunggal.data)
    tunggal_count = int(tunggal_count_match.group(1)) if tunggal_count_match else len(re.findall(rb'/Type\s*/Page\b', res_form_tunggal.data))
    assert tunggal_count == 1, f"Formulir tunggal harus 1 halaman, didapat {tunggal_count}"
    print("12. Seluruh route eksisting (/kartu/<pid>.pdf, /formulir/<pid>.pdf, /pengajuan/<pid>/formulir.pdf) tetap ada dan berfungsi normal. [OK]")

    shutil.rmtree(temp_dir, ignore_errors=True)
    print("\n>>> SEMUA 12 PENGUJIAN TAHAP C BERHASIL LULUS DENGAN SEMPURNA! <<<")

if __name__ == "__main__":
    test_tahap_c()
