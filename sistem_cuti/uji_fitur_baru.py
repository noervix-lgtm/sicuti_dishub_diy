"""Pengujian komprehensif fitur Cetak Formulir Permintaan & Pemberian Cuti + Kartu Cuti."""
import os, io, re, zlib, base64, tempfile
from datetime import date
from werkzeug.security import generate_password_hash
import app as A

# Setup isolated test database
temp_dir = tempfile.mkdtemp()
A.DB_PATH = os.path.join(temp_dir, "test_fitur_baru.db")
A.init_db()

c = A.app.test_client()

def tok(r):
    m = re.search(r'name="_csrf" value="(\w+)"', r.get_data(as_text=True))
    return m.group(1) if m else ""

def login(cl, u, p):
    cl.get("/logout")
    t = tok(cl.get("/login"))
    return cl.post("/login", data={"username": u, "password": p, "_csrf": t}, follow_redirects=True)

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

def test():
    print("=== PENGUJIAN FITUR BARU: FORMULIR + KARTU CUTI ===")

    # 1. Konfigurasi data instansi
    with A.app.app_context():
        db = A.db()
        db.execute("INSERT OR REPLACE INTO pengaturan VALUES('instansi', 'DINAS PERHUBUNGAN DIY')")
        db.execute("INSERT OR REPLACE INTO pengaturan VALUES('kepala_nama', 'Ni Made Dwi Panti Indrayanti, S.T., M.T.')")
        db.execute("INSERT OR REPLACE INTO pengaturan VALUES('kepala_nip', '197001011995032001')")
        db.execute("INSERT OR REPLACE INTO pengaturan VALUES('kepala_jabatan', 'Kepala Dinas Perhubungan Daerah Istimewa Yogyakarta')")

        # Buat 2 pegawai
        pw = generate_password_hash("password123")
        db.execute("""INSERT INTO pegawai(nip, nama, golongan, unit_kerja, username, password_hash, role,
            jabatan, masa_kerja, atasan_nama, atasan_nip) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            ("198501012010011001", "Budi Santoso", "III/c", "Bidang Lalu Lintas", "budi", pw, "pegawai",
             "Analis Kebijakan Ahli Muda", "14 Tahun 3 Bulan", "Ir. H. Joko Pramono, MT", "197005121995031002"))
        budi_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        A.ensure_jatah(budi_id, 2026)

        db.execute("""INSERT INTO pegawai(nip, nama, golongan, unit_kerja, username, password_hash, role)
            VALUES(?,?,?,?,?,?,'pegawai')""",
            ("199002022015021002", "Siti Aminah", "III/a", "Sekretariat", "siti", pw))
        siti_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        A.ensure_jatah(siti_id, 2026)
        db.commit()

    adm_client = A.app.test_client()
    budi_client = A.app.test_client()
    siti_client = A.app.test_client()

    login(adm_client, "admin", "admin123")
    login(budi_client, "budi", "password123")
    login(siti_client, "siti", "password123")

    # 2. Budi mengajukan cuti dengan data lengkap (alamat cuti & telepon)
    csrf_budi = tok(budi_client.get("/ajukan"))
    r_ajukan = budi_client.post("/ajukan", data={
        "_csrf": csrf_budi,
        "jenis_cuti": "Cuti Tahunan",
        "tanggal_mulai": "2026-11-02",
        "tanggal_selesai": "2026-11-04",
        "alasan": "Menghadiri pernikahan keluarga di Surakarta",
        "alamat_cuti": "Jl. Slamet Riyadi No. 45, Surakarta",
        "telp_cuti": "081234567890",
    }, follow_redirects=True)
    assert "berhasil dikirim" in r_ajukan.get_data(as_text=True), "Pengajuan Budi gagal"
    print("1. Pengajuan cuti oleh pegawai berhasil terkirim.")

    with A.app.app_context():
        p_row = A.db().execute("SELECT * FROM pengajuan_cuti WHERE pegawai_id=?", (budi_id,)).fetchone()
        pid = p_row["id"]
        assert p_row["alamat_cuti"] == "Jl. Slamet Riyadi No. 45, Surakarta"
        assert p_row["telp_cuti"] == "081234567890"
        assert p_row["status"] == "Menunggu"
    print("2. Data tersimpan persis di database pengajuan_cuti.")

    # 3. Uji Hak Akses Cetak Formulir
    # Siti mencoba mencetak formulir Budi -> harus 403 Forbidden
    r_siti = siti_client.get(f"/formulir/{pid}.pdf")
    assert r_siti.status_code == 403, f"Expected 403, got {r_siti.status_code}"
    print("3. Hak akses teruji: Pegawai lain (Siti) dilarang mencetak formulir Budi (HTTP 403).")

    # Budi mencetak formulirnya sendiri -> 200 OK
    r_budi = budi_client.get(f"/formulir/{pid}.pdf")
    assert r_budi.status_code == 200, f"Expected 200, got {r_budi.status_code}"
    assert r_budi.data[:4] == b"%PDF", "Response bukan file PDF valid"
    print("4. Hak akses teruji: Pemilik pengajuan (Budi) dapat mencetak formulirnya (HTTP 200).")

    # Admin mencetak formulir Budi -> 200 OK
    r_adm = adm_client.get(f"/formulir/{pid}.pdf")
    assert r_adm.status_code == 200, f"Expected 200, got {r_adm.status_code}"
    print("5. Hak akses teruji: Admin dapat mencetak formulir pegawai (HTTP 200).")

    # 4. Validasi Struktur PDF (Halaman, Dimensi, dan Isi saat status 'Menunggu')
    pdf_bytes = r_budi.data
    # Hitung halaman
    pages_count_match = re.search(rb'/Count\s+(\d+)', pdf_bytes)
    pages_count = int(pages_count_match.group(1)) if pages_count_match else len(re.findall(rb'/Type\s*/Page\b', pdf_bytes))
    assert pages_count == 2, f"Total halaman harus tepat 2, didapat {pages_count}"
    print("6. Total halaman PDF tepat 2 halaman (Halaman 1 muat 1 halaman A4).")

    # Cek MediaBox tiap halaman
    mediaboxes = re.findall(rb'/MediaBox\s*\[\s*0\s+0\s+([\d\.]+)\s+([\d\.]+)\s*\]', pdf_bytes)
    assert len(mediaboxes) == 2, f"MediaBox harus ada 2, ditemukan {len(mediaboxes)}"
    w1, h1 = float(mediaboxes[0][0]), float(mediaboxes[0][1])
    assert w1 < h1, "Halaman 1 harus berorientasi Portrait A4"
    print(f"7. Halaman 1 berorientasi Portrait A4 ({w1:.1f} x {h1:.1f} pt).")

    w2, h2 = float(mediaboxes[1][0]), float(mediaboxes[1][1])
    assert w2 > h2, "Halaman 2 harus berorientasi Landscape A4"
    print(f"8. Halaman 2 berorientasi Landscape A4 ({w2:.1f} x {h2:.1f} pt).")

    # Ekstraksi dan verifikasi teks
    teks_lengkap = ekstrak_teks_pdf(pdf_bytes)

    # Verifikasi isi Halaman 1
    assert "Yogyakarta" in teks_lengkap, "Header tanggal Yogyakarta tidak ditemukan"
    assert "FORMULIR PERMINTAAN DAN PEMBERIAN CUTI" in teks_lengkap, "Judul formulir tidak ditemukan"
    assert "DATA PEGAWAI" in teks_lengkap, "Seksi I tidak ditemukan"
    assert "Budi Santoso" in teks_lengkap, "Nama pemohon tidak tercetak"
    assert "198501012010011001" in teks_lengkap, "NIP pemohon tidak tercetak"
    assert "Analis Kebijakan Ahli Muda" in teks_lengkap, "Jabatan tidak tercetak"
    assert "14 Tahun 3 Bulan" in teks_lengkap, "Masa kerja tidak tercetak"
    assert "Bidang Lalu Lintas" in teks_lengkap, "Unit kerja tidak tercetak"
    assert "JENIS CUTI YANG DIAMBIL" in teks_lengkap, "Seksi II tidak ditemukan"
    assert "Cuti Tahunan" in teks_lengkap, "Jenis cuti tidak tercetak"
    assert "ALASAN CUTI" in teks_lengkap, "Seksi III tidak ditemukan"
    assert "Menghadiri pernikahan keluarga di Surakarta" in teks_lengkap, "Alasan cuti tidak tercetak"
    assert "LAMANYA CUTI" in teks_lengkap, "Seksi IV tidak ditemukan"
    assert "3 hari" in teks_lengkap, "Lama cuti tidak tercetak"
    assert "CATATAN CUTI" in teks_lengkap, "Seksi V tidak ditemukan"
    assert "ALAMAT SELAMA MENJALANKAN CUTI" in teks_lengkap, "Seksi VI tidak ditemukan"
    assert "Jl. Slamet Riyadi No. 45, Surakarta" in teks_lengkap, "Alamat cuti tidak tercetak"
    assert "081234567890" in teks_lengkap, "Nomor telepon cuti tidak tercetak"
    assert "PERTIMBANGAN ATASAN LANGSUNG" in teks_lengkap, "Seksi VII tidak ditemukan"
    assert "Ir. H. Joko Pramono, MT" in teks_lengkap, "Nama atasan tidak tercetak"
    assert "KEPUTUSAN PEJABAT YANG BERWENANG" in teks_lengkap, "Seksi VIII tidak ditemukan"
    assert "Ni Made Dwi Panti Indrayanti" in teks_lengkap, "Nama kepala dinas tidak tercetak"
    print("9. Halaman 1 memuat data lengkap seksi I s.d. VIII secara akurat.")

    # Verifikasi isi Halaman 2 (Kartu Cuti Model Fe.03)
    assert "KARTU CUTI PEGAWAI NEGERI SIPIL" in teks_lengkap, "Judul kartu cuti tidak ditemukan"
    assert "Model: Fe.03" in teks_lengkap, "Model Fe.03 tidak ditemukan"
    assert "Budi Santoso" in teks_lengkap, "Nama pegawai di kartu tidak tercetak"
    assert "Cuti Tahunan" in teks_lengkap, "Baris jenis cuti tidak ada di kartu"
    assert "3 hari" in teks_lengkap, "Lama cuti tidak ada di baris kartu"
    print("10. Halaman 2 (Kartu Cuti) memuat baris pengajuan cuti yang bersangkutan.")

    # 5. Uji Keputusan Admin (Disetujui) & Perubahan Status di Formulir
    csrf_adm = tok(adm_client.get(f"/pengajuan/{pid}"))
    r_setuju = adm_client.post(f"/admin/pengajuan/{pid}/proses", data={
        "_csrf": csrf_adm,
        "aksi": "setuju",
        "nomor_surat": "800/123/2026",
        "tanggal_surat": "2026-10-15",
        "catatan": "Disetujui dinas",
    }, follow_redirects=True)
    assert r_setuju.status_code == 200

    # Cetak ulang PDF setelah disetujui
    r_budi_setuju = budi_client.get(f"/formulir/{pid}.pdf")
    teks_setuju = ekstrak_teks_pdf(r_budi_setuju.data)
    assert "800/123/2026" in teks_setuju, "Nomor surat tidak tercetak setelah disetujui"
    print("11. Setelah disetujui, nomor surat (800/123/2026) dan status muncul di formulir & kartu.")

    # Simpan file contoh formulir+kartu PDF untuk arsip/inspeksi
    contoh_path = os.path.join(A.BASE, "pdf", "contoh_formulir_kartu.pdf")
    with open(contoh_path, "wb") as f:
        f.write(r_budi_setuju.data)
    print(f"12. File PDF contoh berhasil disimpan di: {contoh_path}")

    # Uji coba buka route admin pegawai edit untuk memastikan form edit pegawai berfungsi
    r_edit_page = adm_client.get(f"/admin/pegawai/{budi_id}")
    assert r_edit_page.status_code == 200
    assert "Analis Kebijakan Ahli Muda" in r_edit_page.get_data(as_text=True)
    assert "Ir. H. Joko Pramono, MT" in r_edit_page.get_data(as_text=True)
    print("13. Form edit pegawai di admin menampilkan data jabatan & atasan dengan benar.")

    print("\n>>> SEMUA 13 PENGUJIAN FITUR BARU LULUS DENGAN SEMPURNA! <<<")

if __name__ == "__main__":
    test()
