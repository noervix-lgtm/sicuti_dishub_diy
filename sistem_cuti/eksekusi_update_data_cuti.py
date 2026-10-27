#!/usr/bin/env python3
"""
Skrip pembaruan resmi Data Pegawai dan Sisa Cuti 2026
Memperbarui MySQL (sicuti_dishub) dan SQLite (database.db)
"""
import os
import sys
import math
import shutil
import sqlite3
from datetime import datetime
import pymysql
from werkzeug.security import generate_password_hash
import openpyxl

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
from db_config import (
    get_db, DB_TYPE, SQLITE_DB,
    MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB
)
from data_cuti_baru_60 import DATA_BARU_60

MYSQL_CONFIG = {
    "host": MYSQL_HOST,
    "user": MYSQL_USER,
    "password": MYSQL_PASSWORD,
    "port": MYSQL_PORT,
    "database": MYSQL_DB,
}

def main():
    print("=" * 70)
    print("MEMULAI PROSES PEMBARUAN DATA CUTI DISHUB DIY")
    print("=" * 70)

    # 1. Baca data nominatif.xlsx untuk referensi pelengkap
    nom_path = os.path.join(BASE_DIR, "nominatif.xlsx")
    wb_nom = openpyxl.load_workbook(nom_path, data_only=True)
    sheet_nom = wb_nom.active
    nom_data = {}
    for r in range(3, sheet_nom.max_row + 1):
        nip = str(sheet_nom.cell(r, 2).value or "").strip()
        if nip:
            nom_data[nip] = {
                "unor": str(sheet_nom.cell(r, 1).value or "").strip(),
                "nama": str(sheet_nom.cell(r, 3).value or "").strip(),
                "gol": str(sheet_nom.cell(r, 4).value or "").strip(),
                "jab": str(sheet_nom.cell(r, 5).value or "").strip(),
                "mk": str(sheet_nom.cell(r, 6).value or "").strip(),
                "kj": str(sheet_nom.cell(r, 7).value or "").strip(),
            }

    # Backup SQLite database
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if os.path.exists(SQLITE_DB):
        backup_sqlite = os.path.join(BASE_DIR, f"database_backup_{timestamp}.db")
        shutil.copy2(SQLITE_DB, backup_sqlite)
        print(f"[OK] Backup SQLite tersimpan di: {os.path.basename(backup_sqlite)}")

    # Backup MySQL database tables
    try:
        mysql_conn = pymysql.connect(
            host=MYSQL_CONFIG["host"],
            user=MYSQL_CONFIG["user"],
            password=MYSQL_CONFIG["password"],
            port=MYSQL_CONFIG["port"],
            database=MYSQL_CONFIG["database"],
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor
        )
        with mysql_conn.cursor() as cur:
            cur.execute(f"CREATE TABLE IF NOT EXISTS pegawai_backup_{timestamp} AS SELECT * FROM pegawai")
            cur.execute(f"CREATE TABLE IF NOT EXISTS jatah_cuti_backup_{timestamp} AS SELECT * FROM jatah_cuti")
            mysql_conn.commit()
            print(f"[OK] Backup MySQL tabel pegawai & jatah_cuti tersimpan dengan suffix _{timestamp}")
    except Exception as e:
        print(f"[WARN] Backup MySQL warning: {e}")

    # Pegawai baru yang perlu di-insert
    pegawai_baru_insert = {
        "199612102020121008": {
            "nip": "199612102020121008",
            "nama": "LALU ANUGERAH KEVIN ALGINOLA, S.S.T(TD).",
            "golongan": "Penata Muda Tk. I/III/b",
            "unit_kerja": "SEKRETARIAT, SUBBAGIAN PROGRAM",
            "username": "199612102020121008",
            "role": "pegawai",
            "aktif": 1,
            "jabatan": "Penelaah Teknis Kebijakan",
            "masa_kerja": "05 Tahun 10 Bulan",
            "atasan_nama": "MUHAMMAD SYAIFUL NAZAR S.S.T. (T.D), M.Sc.",
            "atasan_nip": "198908152015021002",
            "kelas_jabatan": "7",
            "tmt_kerja": "2020-12-01"
        },
        "197802142005011001": {
            "nip": "197802142005011001",
            "nama": "VALENTINUS BUDI SANTOSO S.Sos., M.H.",
            "golongan": "Pembina/IV/a",
            "unit_kerja": "BIDANG PENGENDALIAN OPERASIONAL",
            "username": "197802142005011001",
            "role": "pegawai",
            "aktif": 1,
            "jabatan": "Kepala Seksi Pengendalian Operasional Angkutan Jalan",
            "masa_kerja": "21 Tahun 09 Bulan",
            "atasan_nama": "",
            "atasan_nip": "",
            "kelas_jabatan": "9",
            "tmt_kerja": "2005-01-01"
        }
    }

    # NIP yang ada dalam 60 data baru
    nips_60 = {item["nip"] for item in DATA_BARU_60}

    # Fungsi untuk update database (berlaku untuk MySQL maupun SQLite)
    def update_database_instance(conn, is_mysql=True):
        cur = conn.cursor()
        param = "%s" if is_mysql else "?"

        # A. Cek pegawai yang ada
        if is_mysql:
            cur.execute("SELECT id, nip, nama FROM pegawai WHERE role='pegawai'")
            rows = cur.fetchall()
        else:
            cur.execute("SELECT id, nip, nama FROM pegawai WHERE role='pegawai'")
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]

        db_nips = {r["nip"]: r for r in rows if r["nip"]}

        # B. Insert pegawai baru jika belum ada
        for nip, pinfo in pegawai_baru_insert.items():
            if nip not in db_nips:
                pwd_hash = generate_password_hash(nip)
                sql_ins = f"""
                    INSERT INTO pegawai (
                        nip, nama, golongan, unit_kerja, username, password_hash,
                        role, aktif, jabatan, masa_kerja, atasan_nama, atasan_nip,
                        kelas_jabatan, tmt_kerja
                    ) VALUES (
                        {param}, {param}, {param}, {param}, {param}, {param},
                        {param}, {param}, {param}, {param}, {param}, {param},
                        {param}, {param}
                    )
                """
                vals = (
                    pinfo["nip"], pinfo["nama"], pinfo["golongan"], pinfo["unit_kerja"],
                    pinfo["username"], pwd_hash, pinfo["role"], pinfo["aktif"],
                    pinfo["jabatan"], pinfo["masa_kerja"], pinfo["atasan_nama"],
                    pinfo["atasan_nip"], pinfo["kelas_jabatan"], pinfo["tmt_kerja"]
                )
                cur.execute(sql_ins, vals)
                new_id = cur.lastrowid
                db_nips[nip] = {"id": new_id, "nip": nip, "nama": pinfo["nama"]}
                print(f"  [+] Ditambahkan pegawai baru: {nip} - {pinfo['nama']}")

        # C. Nonaktifkan pegawai lama yang TIDAK ada di daftar 60 (aktif = 0)
        for nip, r in db_nips.items():
            if nip not in nips_60:
                cur.execute(f"UPDATE pegawai SET aktif=0 WHERE id={param}", (r["id"],))
                print(f"  [-] Pegawai dinonaktifkan (aktif=0): {nip} - {r['nama']}")

        # D. Update data pegawai untuk 60 orang (nama, golongan, jabatan, aktif=1, kelas_jabatan, masa_kerja)
        for item in DATA_BARU_60:
            nip = item["nip"]
            target_nama = item["nama"]
            target_gol = item["golongan"]
            target_jab = item["jabatan"]
            target_sisa = item["sisa_cuti"]

            nom = nom_data.get(nip, {})
            kj = nom.get("kj", "")
            mk = nom.get("mk", "")

            # Update pegawai
            p_id = db_nips[nip]["id"]
            if kj and mk:
                sql_up = f"""
                    UPDATE pegawai SET
                        nama={param}, golongan={param}, jabatan={param}, aktif=1,
                        kelas_jabatan=COALESCE(NULLIF(kelas_jabatan, ''), {param}),
                        masa_kerja=COALESCE(NULLIF(masa_kerja, ''), {param})
                    WHERE id={param}
                """
                cur.execute(sql_up, (target_nama, target_gol, target_jab, kj, mk, p_id))
            else:
                sql_up = f"""
                    UPDATE pegawai SET
                        nama={param}, golongan={param}, jabatan={param}, aktif=1
                    WHERE id={param}
                """
                cur.execute(sql_up, (target_nama, target_gol, target_jab, p_id))

            # Hitung cuti yang sudah diambil di 2026 (status Disetujui & memotong_jatah=1)
            sql_pakai = f"""
                SELECT COALESCE(SUM(jumlah_hari), 0) AS s FROM pengajuan_cuti
                WHERE pegawai_id={param} AND status='Disetujui' AND memotong_jatah=1
                AND substr(tanggal_mulai, 1, 4)='2026'
            """
            cur.execute(sql_pakai, (p_id,))
            res_pakai = cur.fetchone()
            pakai = (res_pakai["s"] if is_mysql else res_pakai[0]) or 0

            # Hitung formula presisi agar sisa_cuti = target_sisa
            diff = target_sisa + pakai - 12
            if diff >= 0:
                tambahan = diff
                digunakan_awal = 0
            else:
                tambahan = 0
                digunakan_awal = -diff

            total_jatah = 12 + tambahan
            total_digunakan = digunakan_awal + pakai
            sisa_cuti = total_jatah - total_digunakan
            assert sisa_cuti == target_sisa, f"Mismatch sisa_cuti {sisa_cuti} != {target_sisa} for {nip}"
            carry = math.ceil(max(sisa_cuti, 0) / 2)

            # Cek apakah jatah_cuti 2026 sudah ada
            cur.execute(f"SELECT id FROM jatah_cuti WHERE pegawai_id={param} AND tahun=2026", (p_id,))
            j_row = cur.fetchone()

            if j_row:
                j_id = j_row["id"] if is_mysql else j_row[0]
                sql_up_j = f"""
                    UPDATE jatah_cuti SET
                        jatah_dasar=12,
                        tambahan_dari_tahun_sebelumnya={param},
                        total_jatah={param},
                        digunakan_awal={param},
                        total_digunakan={param},
                        sisa_cuti={param},
                        cuti_dibawa_ke_tahun_berikutnya={param}
                    WHERE id={param}
                """
                cur.execute(sql_up_j, (tambahan, total_jatah, digunakan_awal, total_digunakan, sisa_cuti, carry, j_id))
            else:
                sql_ins_j = f"""
                    INSERT INTO jatah_cuti (
                        pegawai_id, tahun, jatah_dasar, tambahan_dari_tahun_sebelumnya,
                        total_jatah, digunakan_awal, total_digunakan, sisa_cuti,
                        cuti_dibawa_ke_tahun_berikutnya
                    ) VALUES (
                        {param}, 2026, 12, {param},
                        {param}, {param}, {param}, {param},
                        {param}
                    )
                """
                cur.execute(sql_ins_j, (p_id, tambahan, total_jatah, digunakan_awal, total_digunakan, sisa_cuti, carry))

        conn.commit()

    # Eksekusi pada MySQL
    print("\n--- Memperbarui Database MySQL (sicuti_dishub) ---")
    try:
        mysql_conn = pymysql.connect(
            host=MYSQL_CONFIG["host"],
            user=MYSQL_CONFIG["user"],
            password=MYSQL_CONFIG["password"],
            port=MYSQL_CONFIG["port"],
            database=MYSQL_CONFIG["database"],
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor
        )
        update_database_instance(mysql_conn, is_mysql=True)
        mysql_conn.close()
        print("[BERHASIL] Database MySQL berhasil diperbarui!")
    except Exception as e:
        print(f"[ERROR] Gagal memperbarui MySQL: {e}")

    # Eksekusi pada SQLite
    print("\n--- Memperbarui Database SQLite (database.db) ---")
    try:
        sqlite_conn = sqlite3.connect(SQLITE_DB)
        update_database_instance(sqlite_conn, is_mysql=False)
        sqlite_conn.close()
        print("[BERHASIL] Database SQLite berhasil diperbarui!")
    except Exception as e:
        print(f"[ERROR] Gagal memperbarui SQLite: {e}")

    # Buat Excel Rekap Data Cuti Terbaru 2026
    print("\n--- Membuat Berkas Excel Data Cuti Terbaru 2026 ---")
    wb_out = openpyxl.Workbook()
    ws_out = wb_out.active
    ws_out.title = "Data Cuti 2026"

    headers = ["NO", "NIP", "NAMA", "GOLONGAN", "JABATAN", "JATAH DASAR", "TAMBAHAN DARI TH SEBELUMNYA", "TOTAL JATAH", "DIGUNAKAN AWAL", "SISA CUTI 2026"]
    ws_out.append(headers)

    # Style header
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")
    thin_border = Border(
        left=Side(style="thin", color="CCCCCC"),
        right=Side(style="thin", color="CCCCCC"),
        top=Side(style="thin", color="CCCCCC"),
        bottom=Side(style="thin", color="CCCCCC")
    )

    for col_num in range(1, len(headers) + 1):
        cell = ws_out.cell(1, col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align

    for item in DATA_BARU_60:
        target_sisa = item["sisa_cuti"]
        diff = target_sisa - 12
        tambahan = max(diff, 0)
        dig_awal = max(-diff, 0)
        tot_jatah = 12 + tambahan
        ws_out.append([
            item["no"],
            item["nip"],
            item["nama"],
            item["golongan"],
            item["jabatan"],
            12,
            tambahan,
            tot_jatah,
            dig_awal,
            target_sisa
        ])

    for r in range(2, ws_out.max_row + 1):
        for c in range(1, len(headers) + 1):
            cell = ws_out.cell(r, c)
            cell.border = thin_border
            if c in (1, 6, 7, 8, 9, 10):
                cell.alignment = center_align
            else:
                cell.alignment = left_align

    # Adjust column widths
    for col in ws_out.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws_out.column_dimensions[col_letter].width = max(max_len + 3, 10)

    excel_out_path = os.path.join(BASE_DIR, "data_cuti_terbaru_2026.xlsx")
    wb_out.save(excel_out_path)
    print(f"[OK] Berkas Excel tersimpan di: {excel_out_path}")

    print("\n" + "=" * 70)
    print("PEMBARUAN SELESAI DENGAN SUKSES!")
    print("=" * 70)

if __name__ == "__main__":
    main()
