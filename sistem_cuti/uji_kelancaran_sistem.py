#!/usr/bin/env python3
"""
Pengujian komprehensif kelancaran aplikasi SICUTI DISHUB DIY.
Menguji koneksi database aktif, login admin, dashboard admin, daftar pegawai,
daftar jatah cuti, login pegawai baru, dan dashboard pegawai.
"""
import os
import sys
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import app as A
from db_config import get_db, DB_TYPE

client = A.app.test_client()

def get_csrf(html):
    m = re.search(r'name="_csrf"\s+value="([^"]+)"', html)
    if m:
        return m.group(1)
    m = re.search(r'value="([^"]+)"\s+name="_csrf"', html)
    return m.group(1) if m else ""

def test_system():
    print("=" * 70)
    print("UJI KELANCARAN SISTEM SICUTI DISHUB DIY")
    print(f"Tipe Database Aktif: {DB_TYPE}")
    print("=" * 70)

    # 1. Cek Database
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM pegawai WHERE role='pegawai' AND aktif=1")
    r_akt = cur.fetchone()
    total_aktif = r_akt["c"] if isinstance(r_akt, dict) else r_akt[0]
    print(f"[1] Pegawai Aktif di DB: {total_aktif} (Target: 60)")
    assert total_aktif == 60, f"Total pegawai aktif {total_aktif} != 60"

    cur.execute("SELECT COUNT(*) AS c FROM jatah_cuti WHERE tahun=2026")
    r_jat = cur.fetchone()
    total_jatah = r_jat["c"] if isinstance(r_jat, dict) else r_jat[0]
    print(f"[2] Total Record Jatah Cuti 2026: {total_jatah}")
    assert total_jatah >= 60, f"Record jatah cuti {total_jatah} < 60"
    con.close()

    # 2. Uji Login Admin
    c_admin = A.app.test_client()
    resp_login_page = c_admin.get("/login")
    assert resp_login_page.status_code == 200, "Halaman login gagal dibuka!"
    csrf = get_csrf(resp_login_page.get_data(as_text=True))
    
    resp_login = c_admin.post("/login", data={
        "username": "admin",
        "password": "admin123",
        "_csrf": csrf
    }, follow_redirects=True)
    assert resp_login.status_code == 200, "Login admin gagal!"
    body_admin = resp_login.get_data(as_text=True)
    assert "Administrator" in body_admin or "Dashboard" in body_admin, "Dashboard admin tidak termuat!"
    print("[3] Login Administrator & Dashboard Admin: BERJALAN LANCAR (Status 200)")

    # 3. Uji Halaman Pegawai Admin
    resp_pegawai = c_admin.get("/admin/pegawai")
    assert resp_pegawai.status_code == 200, "Halaman /admin/pegawai gagal dibuka!"
    body_peg = resp_pegawai.get_data(as_text=True)
    assert "CHRESTINA ERNI WIDYASTUTI" in body_peg, "Nama Kepala Dinas tidak muncul di daftar!"
    assert "LALU ANUGERAH KEVIN ALGINOLA" in body_peg, "Pegawai baru Lalu Kevin tidak muncul di daftar!"
    assert "VALENTINUS BUDI SANTOSO" in body_peg, "Pegawai baru Valentinus tidak muncul di daftar!"
    print("[4] Halaman /admin/pegawai (Daftar Pegawai): BERJALAN LANCAR (Status 200)")

    # 4. Uji Halaman Kartu Cuti Admin (/admin/kartu)
    resp_kartu = c_admin.get("/admin/kartu")
    assert resp_kartu.status_code == 200, "Halaman /admin/kartu gagal dibuka!"
    body_kartu = resp_kartu.get_data(as_text=True)
    assert "CHRESTINA ERNI WIDYASTUTI" in body_kartu, "Pegawai tidak muncul di rekap kartu cuti!"
    print("[5] Halaman /admin/kartu (Rekap Jatah & Kartu Cuti): BERJALAN LANCAR (Status 200)")

    # 4b. Uji Halaman Riwayat Cuti Admin (/admin/riwayat)
    resp_riwayat = c_admin.get("/admin/riwayat")
    assert resp_riwayat.status_code == 200, "Halaman /admin/riwayat gagal dibuka!"
    print("[5b] Halaman /admin/riwayat (Riwayat Pengajuan Cuti): BERJALAN LANCAR (Status 200)")

    # 5. Uji Halaman Pengajuan Admin
    resp_peng = c_admin.get("/admin/pengajuan")
    assert resp_peng.status_code == 200, "Halaman /admin/pengajuan gagal dibuka!"
    print("[6] Halaman /admin/pengajuan (Pengajuan Cuti): BERJALAN LANCAR (Status 200)")

    # 6. Uji Halaman Pengaturan Admin
    resp_set = c_admin.get("/admin/pengaturan")
    assert resp_set.status_code == 200, "Halaman /admin/pengaturan gagal dibuka!"
    print("[7] Halaman /admin/pengaturan (Pengaturan Sistem): BERJALAN LANCAR (Status 200)")

    # 7. Uji Login Pegawai Baru 1: Lalu Anugerah Kevin Alginola
    c_kevin = A.app.test_client()
    resp_lp_k = c_kevin.get("/login")
    csrf_k = get_csrf(resp_lp_k.get_data(as_text=True))
    resp_log_k = c_kevin.post("/login", data={
        "username": "199612102020121008",
        "password": "199612102020121008",
        "_csrf": csrf_k
    }, follow_redirects=True)
    assert resp_log_k.status_code == 200, "Login Kevin gagal!"
    body_k = resp_log_k.get_data(as_text=True)
    assert "KEVIN" in body_k.upper(), "Dashboard Kevin tidak menampilkan nama Kevin!"
    assert "16" in body_k, "Sisa cuti 16 hari tidak tampil di dashboard Kevin!"
    print("[8] Akun Pegawai Baru Lalu Kevin (NIP 199612102020121008): LOGIN & DASHBOARD LANCAR (Sisa Cuti: 16)")

    # 8. Uji Login Pegawai Baru 2: Valentinus Budi Santoso
    c_val = A.app.test_client()
    resp_lp_v = c_val.get("/login")
    csrf_v = get_csrf(resp_lp_v.get_data(as_text=True))
    resp_log_v = c_val.post("/login", data={
        "username": "197802142005011001",
        "password": "197802142005011001",
        "_csrf": csrf_v
    }, follow_redirects=True)
    assert resp_log_v.status_code == 200, "Login Valentinus gagal!"
    body_v = resp_log_v.get_data(as_text=True)
    assert "VALENTINUS" in body_v.upper(), "Dashboard Valentinus tidak menampilkan namanya!"
    assert "17" in body_v, "Sisa cuti 17 hari tidak tampil di dashboard Valentinus!"
    print("[9] Akun Pegawai Baru Valentinus (NIP 197802142005011001): LOGIN & DASHBOARD LANCAR (Sisa Cuti: 17)")

    # 9. Uji Login Pegawai ASN PPPK (Golongan VII: Bagas Hariya Mardiko)
    c_bagas = A.app.test_client()
    resp_lp_b = c_bagas.get("/login")
    csrf_b = get_csrf(resp_lp_b.get_data(as_text=True))
    resp_log_b = c_bagas.post("/login", data={
        "username": "199208172025211009",
        "password": "199208172025211009",
        "_csrf": csrf_b
    }, follow_redirects=True)
    assert resp_log_b.status_code == 200, "Login Bagas gagal!"
    body_b = resp_log_b.get_data(as_text=True)
    assert "BAGAS" in body_b.upper(), "Dashboard Bagas tidak menampilkan namanya!"
    assert "11" in body_b, "Sisa cuti 11 hari tidak tampil di dashboard Bagas!"
    print("[10] Akun Pegawai PPPK Bagas (NIP 199208172025211009): LOGIN & DASHBOARD LANCAR (Sisa Cuti: 11)")

    # 10. Uji Form Pengajuan Cuti (Halaman /ajukan)
    resp_ajukan = c_kevin.get("/ajukan")
    assert resp_ajukan.status_code == 200, "Halaman formulir ajukan cuti gagal dibuka!"
    print("[11] Halaman Pengajuan Cuti (/ajukan): BERJALAN LANCAR (Status 200)")

    # 11. Uji Pembuatan Kartu Cuti PDF (ReportLab) untuk Pegawai Baru
    with A.app.app_context():
        p_row = A.db().execute("SELECT id FROM pegawai WHERE nip='199612102020121008'").fetchone()
        pid_kevin = p_row["id"]
    resp_pdf = c_kevin.get(f"/kartu/{pid_kevin}.pdf")
    assert resp_pdf.status_code == 200, "Generate PDF kartu cuti gagal!"
    assert resp_pdf.headers.get("Content-Type") == "application/pdf", "Content-Type bukan PDF!"
    print(f"[12] Generate PDF Kartu Cuti (Lalu Kevin): BERJALAN LANCAR (Ukuran: {len(resp_pdf.data)} bytes)")

    print("\n" + "=" * 70)
    print("HASIL PENGUJIAN: SEMUA FITUR DAN DATA BERJALAN DENGAN SEMPURNA!")
    print("=" * 70)

if __name__ == "__main__":
    test_system()
